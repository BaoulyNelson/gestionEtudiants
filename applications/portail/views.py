from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
import datetime

from applications.comptes.models import Utilisateur, Etudiant, Professeur
from applications.portail.models import Livre, Personnel, NewsletterInscription, SiteSettings, Examen
from applications.cours.models import Cours, SectionCours
from applications.departements.models import Departement
from applications.articles.models import Article, Evenement, Annonce
from applications.inscriptions.models import Inscription

from .forms import ExamenForm, FormulaireParametresSite,FormulairePersonnel,FormulaireLivre
from utilitaires.roles import est_administrateur, est_etudiant, est_professeur, est_professeur_ou_admin
from .models import Personnel, Livre
# ============================================================
# À INTÉGRER dans applications/portail/views.py
# Remplacer les 4 vues livre existantes par ce bloc complet
# ============================================================

import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.utils import timezone

from .models import Livre, Emprunt, Reservation
from utilitaires.roles import est_administrateur
from applications.notifications.models import Notification
# ──────────────────────────────────────────────────────────────
# ACCUEIL
# ──────────────────────────────────────────────────────────────

def vue_accueil(request):
    """Page d'accueil publique"""
    if request.user.is_authenticated:
        return redirect('comptes:tableau_bord')

    aujourdhui = datetime.date.today()
    annonces   = Annonce.objects.filter(est_active=True).order_by('-date_publication')[:4]
    evenements = Evenement.objects.filter(date_fin__date__gte=aujourdhui).order_by('date_debut')[:4]

    return render(request, 'index.html', {
        'annonces':   annonces,
        'evenements': evenements,
        'examens':    None,
    })


# ──────────────────────────────────────────────────────────────
# EXAMENS
# ──────────────────────────────────────────────────────────────

@login_required
def vue_liste_examens(request):
    """Liste des examens filtrée selon le rôle de l'utilisateur"""
    filtre = request.GET.get('filtre', 'tous')

    # ✅ Filtrage par rôle — chaque utilisateur ne voit que ce qui le concerne
    if request.user.is_superuser or request.user.est_administrateur():
        # Admin : tous les examens
        qs = Examen.objects.select_related('section_cours__cours', 'section_cours__cours__departement')
    elif request.user.est_professeur():
        # Professeur : examens de ses sections uniquement
        sections = request.user.profil_professeur.sections_cours.all()
        qs = Examen.objects.filter(
            section_cours__in=sections
        ).select_related('section_cours__cours', 'section_cours__cours__departement')
    else:
        # Étudiant : examens des sections auxquelles il est inscrit
        inscriptions = Inscription.objects.filter(
            etudiant=request.user.profil_etudiant,
            statut__in=Inscription.STATUTS_ACTIFS,
        ).values_list('section_cours', flat=True)
        qs = Examen.objects.filter(
            section_cours__in=inscriptions
        ).select_related('section_cours__cours', 'section_cours__cours__departement')

    examens_en_cours = qs.filter(statut='en_cours').order_by('date')
    examens_a_venir  = qs.filter(statut='a_venir').order_by('date')
    examens_termines = qs.filter(statut='termine').order_by('-date')[:10]

    return render(request, 'portail/examens/liste.html', {
        'examens_en_cours': examens_en_cours,
        'examens_a_venir':  examens_a_venir,
        'examens_termines': examens_termines,
        'filtre':           filtre,
    })


@login_required
@user_passes_test(est_professeur_ou_admin)
def vue_creer_examen(request):
    """Planifier un nouvel examen lié à une section de cours"""
    formulaire = ExamenForm(request.POST or None, user=request.user)

    if request.method == 'POST' and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Examen planifié avec succès.")
        return redirect('portail:liste_examens')

    return render(request, 'portail/examens/formulaire.html', {
        'formulaire': formulaire,
        'action':     'Planifier un examen',
        'examen':     None,
    })


@login_required
@user_passes_test(est_professeur_ou_admin)
def vue_modifier_examen(request, examen_id):
    """Modifier un examen existant"""
    examen     = get_object_or_404(Examen, id=examen_id)
    formulaire = ExamenForm(request.POST or None, instance=examen, user=request.user)

    if request.method == 'POST' and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Examen modifié avec succès.")
        return redirect('portail:liste_examens')

    return render(request, 'portail/examens/formulaire.html', {
        'formulaire': formulaire,
        'action':     "Modifier l'examen",
        'examen':     examen,
    })


@login_required
@user_passes_test(est_administrateur)
def vue_supprimer_examen(request, examen_id):
    """Supprimer un examen (admin seulement)"""
    examen = get_object_or_404(Examen, id=examen_id)

    if request.method == 'POST':
        examen.delete()
        messages.success(request, "Examen supprimé.")
        return redirect('portail:liste_examens')

    return render(request, 'portail/examens/confirmer_suppression.html', {
        'examen': examen,
    })


# ──────────────────────────────────────────────────────────────
# PARAMÈTRES SITE
# ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(est_administrateur)
def vue_parametres_site(request):
    site = SiteSettings.get()
    form = FormulaireParametresSite(
        request.POST or None,
        request.FILES or None,
        instance=site,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Paramètres mis à jour avec succès.")
        return redirect("portail:parametres_site")
    return render(request, "portail/parametres_site.html", {"form": form, "site": site})


# ──────────────────────────────────────────────────────────────
# RECHERCHE GLOBALE
# ──────────────────────────────────────────────────────────────

def recherche_globale(request):
    requete         = request.GET.get('q', '').strip()
    resultats       = {}
    total_resultats = 0

    if len(requete) >= 2:

        utilisateurs = Utilisateur.objects.filter(
            Q(first_name__icontains=requete)
            | Q(last_name__icontains=requete)
            | Q(email__icontains=requete)
        )[:10]
        if utilisateurs:
            resultats['utilisateurs'] = {
                'titre': 'Utilisateurs', 'items': utilisateurs,
                'nombre': utilisateurs.count(), 'icone': 'user',
            }
            total_resultats += utilisateurs.count()

        etudiants = Etudiant.objects.filter(
            Q(utilisateur__first_name__icontains=requete)
            | Q(utilisateur__last_name__icontains=requete)
            | Q(utilisateur__email__icontains=requete)
            | Q(numero_etudiant__icontains=requete)
        ).select_related('utilisateur')[:10]

        professeurs = Professeur.objects.filter(
            Q(utilisateur__first_name__icontains=requete)
            | Q(utilisateur__last_name__icontains=requete)
            | Q(specialite__icontains=requete)
            | Q(identifiant_professeur__icontains=requete)
        ).select_related('utilisateur', 'departement')[:10]

        departements = Departement.objects.filter(
            Q(nom__icontains=requete)
            | Q(code__icontains=requete)
            | Q(description__icontains=requete)
        )[:10]

        cours = Cours.objects.filter(
            Q(code__icontains=requete)
            | Q(nom__icontains=requete)
            | Q(description__icontains=requete)
        ).select_related('departement')[:10]

        articles = Article.objects.filter(
            Q(titre__icontains=requete)
            | Q(contenu__icontains=requete)
            | Q(auteur__icontains=requete)
        )[:10]
        if articles:
            resultats['articles'] = {
                'titre': 'Articles', 'items': articles,
                'nombre': articles.count(), 'icone': 'newspaper',
            }
            total_resultats += articles.count()

        evenements = Evenement.objects.filter(
            Q(titre__icontains=requete)
            | Q(description__icontains=requete)
            | Q(lieu__icontains=requete)
        )[:10]
        if evenements:
            resultats['evenements'] = {
                'titre': 'Événements', 'items': evenements,
                'nombre': evenements.count(), 'icone': 'calendar',
            }
            total_resultats += evenements.count()

        livres = Livre.objects.filter(
            Q(titre__icontains=requete) | Q(auteur__icontains=requete)
        )[:10]
        if livres:
            resultats['livres'] = {
                'titre': 'Bibliothèque', 'items': livres,
                'nombre': livres.count(), 'icone': 'book',
            }
            total_resultats += livres.count()



        annonces = Annonce.objects.filter(
            Q(titre__icontains=requete) | Q(contenu__icontains=requete)
        )[:10]
        if annonces:
            resultats['annonces'] = {
                'titre': 'Annonces', 'items': annonces,
                'nombre': annonces.count(), 'icone': 'megaphone',
            }
            total_resultats += annonces.count()

        membres_personnel = Personnel.objects.filter(
            Q(nom__icontains=requete) | Q(poste__icontains=requete)
        )[:10]
        if membres_personnel:
            resultats['personnel'] = {
                'titre': 'Personnel', 'items': membres_personnel,
                'nombre': membres_personnel.count(), 'icone': 'id-card',
            }
            total_resultats += membres_personnel.count()



    return render(request, 'portail/recherche_globale.html', {
        'requete':         requete,
        'resultats':       resultats,
        'total_resultats': total_resultats,
    })


# ──────────────────────────────────────────────────────────────
# NEWSLETTER
# ──────────────────────────────────────────────────────────────

def vue_newsletter(request):
    contexte = {"inscrit": False, "erreur": None, "nom_inscrit": ""}

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        nom   = request.POST.get("nom", "").strip()

        if not email:
            contexte["erreur"] = "L'adresse email est obligatoire."
        else:
            obj, created = NewsletterInscription.objects.get_or_create(
                email=email, defaults={"nom": nom}
            )
            if created:
                contexte["inscrit"]     = True
                contexte["nom_inscrit"] = nom or email
            else:
                contexte["erreur"] = "Cette adresse email est déjà inscrite."

    return render(request, "portail/newsletter.html", contexte)






# ── Personnel ────────────────────────────────────────────────────────────────

@login_required
def vue_liste_personnel(request):
    membres = Personnel.objects.select_related("departement").order_by("poste", "nom")
    return render(request, "portail/personnel/liste.html", {"membres": membres})


@login_required
@user_passes_test(est_administrateur)
def vue_creer_personnel(request):
    formulaire = FormulairePersonnel(request.POST or None, request.FILES or None)
    if request.method == "POST" and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Membre du personnel ajouté avec succès.")
        return redirect("portail:liste_personnel")
    return render(request, "portail/personnel/formulaire.html", {
        "formulaire": formulaire,
        "titre": "Ajouter un membre du personnel",
    })


@login_required
@user_passes_test(est_administrateur)
def vue_modifier_personnel(request, personnel_id):
    membre = get_object_or_404(Personnel, id=personnel_id)
    formulaire = FormulairePersonnel(
        request.POST or None, request.FILES or None, instance=membre
    )
    if request.method == "POST" and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Membre du personnel modifié avec succès.")
        return redirect("portail:liste_personnel")
    return render(request, "portail/personnel/formulaire.html", {
        "formulaire": formulaire,
        "titre": f"Modifier — {membre.nom}",
        "membre": membre,
    })


@login_required
@user_passes_test(est_administrateur)
def vue_supprimer_personnel(request, personnel_id):
    membre = get_object_or_404(Personnel, id=personnel_id)
    if request.method == "POST":
        membre.delete()
        messages.success(request, f"« {membre.nom} » supprimé.")
        return redirect("portail:liste_personnel")
    return render(request, "portail/personnel/supprimer.html", {"membre": membre})


# ── Livres ───────────────────────────────────────────────────────────────────




# ── Helpers ─────────────────────────────────────────────────────────────────

def _notifier(utilisateur, titre, message, lien=''):
    Notification.objects.create(
        utilisateur=utilisateur,
        type_notification='livre',
        titre=titre,
        message=message,
        lien=lien,
    )


def _activer_prochaine_reservation(livre):
    """Notifie le prochain en liste d'attente quand un exemplaire se libère."""
    prochaine = (
        livre.reservations
        .filter(statut='en_attente')
        .order_by('date_reservation')
        .first()
    )
    if prochaine:
        prochaine.notifier_disponible()
        _notifier(
            prochaine.utilisateur,
            titre=f'"{livre.titre}" est disponible pour vous',
            message=(
                f'Bonne nouvelle ! Le livre « {livre.titre} » que vous avez réservé '
                f'est maintenant disponible. Vous avez {Reservation.DELAI_DISPONIBILITE_JOURS} jours '
                f'pour venir le récupérer à la médiathèque.'
            ),
            lien='/portail/livres/',
        )


# ── Catalogue ────────────────────────────────────────────────────────────────

@login_required
def vue_liste_livres(request):
    q         = request.GET.get('q', '').strip()
    categorie = request.GET.get('categorie', '')
    dispo     = request.GET.get('dispo', '')

    livres = Livre.objects.prefetch_related('emprunts', 'reservations')

    if q:
        livres = livres.filter(titre__icontains=q) | livres.filter(auteur__icontains=q)
        livres = livres.distinct()
    if categorie:
        livres = livres.filter(categorie=categorie)
    if dispo == '1':
        # On filtre côté Python car disponible est une property
        livres = [l for l in livres if l.disponible]

    # Mes emprunts en cours + réservations actives (pour les badges)
    mes_emprunts_ids     = set()
    mes_reservations_ids = set()
    if request.user.is_authenticated:
        mes_emprunts_ids = set(
            Emprunt.objects.filter(utilisateur=request.user, statut__in=['en_cours', 'en_retard'])
            .values_list('livre_id', flat=True)
        )
        mes_reservations_ids = set(
            Reservation.objects.filter(utilisateur=request.user, statut__in=['en_attente', 'disponible'])
            .values_list('livre_id', flat=True)
        )

    return render(request, 'portail/livres/liste.html', {
        'livres':              livres,
        'categories':          Livre.CHOIX_CATEGORIE,
        'q':                   q,
        'categorie_filtre':    categorie,
        'dispo_filtre':        dispo,
        'mes_emprunts_ids':    mes_emprunts_ids,
        'mes_reservations_ids': mes_reservations_ids,
    })


@login_required
def vue_detail_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)
    mon_emprunt = Emprunt.objects.filter(
        utilisateur=request.user, livre=livre, statut__in=['en_cours', 'en_retard']
    ).first()
    ma_reservation = Reservation.objects.filter(
        utilisateur=request.user, livre=livre, statut__in=['en_attente', 'disponible']
    ).first()
    file_attente = livre.reservations.filter(statut='en_attente').count()

    return render(request, 'portail/livres/detail.html', {
        'livre':          livre,
        'mon_emprunt':    mon_emprunt,
        'ma_reservation': ma_reservation,
        'file_attente':   file_attente,
    })


# ── Emprunts ─────────────────────────────────────────────────────────────────

@login_required
def vue_emprunter(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)

    # Vérifications
    if not livre.disponible:
        messages.error(request, "Ce livre n'a plus d'exemplaires disponibles.")
        return redirect('portail:detail_livre', livre_id=livre_id)

    deja = Emprunt.objects.filter(
        utilisateur=request.user, livre=livre, statut__in=['en_cours', 'en_retard']
    ).exists()
    if deja:
        messages.warning(request, "Vous avez déjà ce livre en votre possession.")
        return redirect('portail:detail_livre', livre_id=livre_id)

    if request.method == 'POST':
        duree = int(request.POST.get('duree_jours', Emprunt.DUREE_DEFAUT_JOURS))
        duree = max(1, min(duree, 30))  # entre 1 et 30 jours
        aujourd_hui = datetime.date.today()

        emprunt = Emprunt.objects.create(
            utilisateur=request.user,
            livre=livre,
            date_emprunt=aujourd_hui,
            date_retour_prevue=aujourd_hui + datetime.timedelta(days=duree),
        )

        # Annuler la réservation si elle en avait une
        Reservation.objects.filter(
            utilisateur=request.user, livre=livre, statut__in=['en_attente', 'disponible']
        ).update(statut='annulee')

        _notifier(
            request.user,
            titre=f'Emprunt confirmé : « {livre.titre} »',
            message=(
                f'Vous avez emprunté « {livre.titre} » le {aujourd_hui.strftime("%d/%m/%Y")}. '
                f'Retour prévu le {emprunt.date_retour_prevue.strftime("%d/%m/%Y")}.'
            ),
            lien='/portail/livres/mes-emprunts/',
        )

        messages.success(request, f"Emprunt de « {livre.titre} » enregistré. Retour prévu le {emprunt.date_retour_prevue.strftime('%d/%m/%Y')}.")
        return redirect('portail:mes_emprunts')

    return render(request, 'portail/livres/confirmer_emprunt.html', {
        'livre': livre,
        'duree_defaut': Emprunt.DUREE_DEFAUT_JOURS,
    })


@login_required
def vue_retourner(request, emprunt_id):
    emprunt = get_object_or_404(Emprunt, id=emprunt_id)

    # Seul l'emprunteur ou un admin peut retourner
    if emprunt.utilisateur != request.user and not request.user.est_administrateur():
        return HttpResponseForbidden()

    if emprunt.statut == 'rendu':
        messages.warning(request, "Ce livre a déjà été retourné.")
        return redirect('portail:mes_emprunts')

    if request.method == 'POST':
        emprunt.statut = 'rendu'
        emprunt.date_retour_effective = datetime.date.today()
        emprunt.save()

        _notifier(
            emprunt.utilisateur,
            titre=f'Retour enregistré : « {emprunt.livre.titre} »',
            message=f'Le retour de « {emprunt.livre.titre} » a été enregistré le {datetime.date.today().strftime("%d/%m/%Y")}. Merci !',
            lien='/portail/livres/mes-emprunts/',
        )

        # Notifier le prochain en liste d'attente
        _activer_prochaine_reservation(emprunt.livre)

        messages.success(request, f"Retour de « {emprunt.livre.titre} » enregistré.")
        return redirect('portail:mes_emprunts' if not request.user.est_administrateur() else 'portail:gestion_emprunts')

    return render(request, 'portail/livres/confirmer_retour.html', {'emprunt': emprunt})


@login_required
def vue_mes_emprunts(request):
    emprunts_actifs = Emprunt.objects.filter(
        utilisateur=request.user, statut__in=['en_cours', 'en_retard']
    ).select_related('livre').order_by('date_retour_prevue')

    historique = Emprunt.objects.filter(
        utilisateur=request.user, statut='rendu'
    ).select_related('livre').order_by('-date_retour_effective')[:20]

    mes_reservations = Reservation.objects.filter(
        utilisateur=request.user, statut__in=['en_attente', 'disponible']
    ).select_related('livre').order_by('date_reservation')

    return render(request, 'portail/livres/mes_emprunts.html', {
        'emprunts_actifs':  emprunts_actifs,
        'historique':       historique,
        'mes_reservations': mes_reservations,
    })


# ── Réservations ─────────────────────────────────────────────────────────────

@login_required
def vue_reserver(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)

    if livre.disponible:
        messages.info(request, "Ce livre est disponible — vous pouvez directement l'emprunter.")
        return redirect('portail:detail_livre', livre_id=livre_id)

    deja_emprunt = Emprunt.objects.filter(
        utilisateur=request.user, livre=livre, statut__in=['en_cours', 'en_retard']
    ).exists()
    if deja_emprunt:
        messages.warning(request, "Vous avez déjà ce livre en votre possession.")
        return redirect('portail:detail_livre', livre_id=livre_id)

    if request.method == 'POST':
        try:
            Reservation.objects.create(utilisateur=request.user, livre=livre)
            messages.success(request, f"Réservation enregistrée pour « {livre.titre} ». Vous serez notifié dès qu'un exemplaire se libère.")
        except IntegrityError:
            messages.warning(request, "Vous avez déjà une réservation active pour ce livre.")
        return redirect('portail:mes_emprunts')

    position = livre.reservations.filter(statut='en_attente').count() + 1
    return render(request, 'portail/livres/confirmer_reservation.html', {
        'livre':    livre,
        'position': position,
    })


@login_required
def vue_annuler_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, utilisateur=request.user)
    if request.method == 'POST':
        reservation.statut = 'annulee'
        reservation.save()
        messages.success(request, f"Réservation pour « {reservation.livre.titre} » annulée.")
    return redirect('portail:mes_emprunts')


# ── Administration ────────────────────────────────────────────────────────────

@login_required
@user_passes_test(est_administrateur)
def vue_gestion_emprunts(request):
    """Vue admin : tous les emprunts en cours + retards."""
    statut = request.GET.get('statut', '')
    q      = request.GET.get('q', '').strip()

    emprunts = Emprunt.objects.select_related('utilisateur', 'livre').order_by('-date_emprunt')

    if statut:
        emprunts = emprunts.filter(statut=statut)
    if q:
        emprunts = emprunts.filter(
            livre__titre__icontains=q
        ) | emprunts.filter(
            utilisateur__first_name__icontains=q
        ) | emprunts.filter(
            utilisateur__last_name__icontains=q
        )
        emprunts = emprunts.distinct()

    # Statistiques rapides
    stats = {
        'en_cours':  Emprunt.objects.filter(statut='en_cours').count(),
        'en_retard': Emprunt.objects.filter(statut='en_retard').count(),
        'rendus_mois': Emprunt.objects.filter(
            statut='rendu',
            date_retour_effective__month=datetime.date.today().month
        ).count(),
    }

    return render(request, 'portail/livres/gestion_emprunts.html', {
        'emprunts': emprunts,
        'stats':    stats,
        'statut_filtre': statut,
        'q': q,
    })


@login_required
@user_passes_test(est_administrateur)
def vue_enregistrer_retour_admin(request, emprunt_id):
    """Admin enregistre un retour physique."""
    emprunt = get_object_or_404(Emprunt, id=emprunt_id)
    if request.method == 'POST':
        emprunt.statut = 'rendu'
        emprunt.date_retour_effective = datetime.date.today()
        emprunt.save()
        _activer_prochaine_reservation(emprunt.livre)
        messages.success(request, f"Retour de « {emprunt.livre.titre} » enregistré pour {emprunt.utilisateur.get_full_name()}.")
    return redirect('portail:gestion_emprunts')


# ── CRUD Livre (admin) ────────────────────────────────────────────────────────

@login_required
@user_passes_test(est_administrateur)
def vue_creer_livre(request):
    from .forms import FormulaireLivre
    formulaire = FormulaireLivre(request.POST or None, request.FILES or None)
    if request.method == 'POST' and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Livre ajouté avec succès.")
        return redirect('portail:liste_livres')
    return render(request, 'portail/livres/formulaire.html', {
        'formulaire': formulaire,
        'titre': 'Ajouter un livre',
    })


@login_required
@user_passes_test(est_administrateur)
def vue_modifier_livre(request, livre_id):
    from .forms import FormulaireLivre
    livre = get_object_or_404(Livre, id=livre_id)
    formulaire = FormulaireLivre(request.POST or None, request.FILES or None, instance=livre)
    if request.method == 'POST' and formulaire.is_valid():
        formulaire.save()
        messages.success(request, "Livre modifié avec succès.")
        return redirect('portail:liste_livres')
    return render(request, 'portail/livres/formulaire.html', {
        'formulaire': formulaire,
        'titre': f'Modifier — {livre.titre}',
        'livre': livre,
    })


@login_required
@user_passes_test(est_administrateur)
def vue_supprimer_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)
    if request.method == 'POST':
        livre.delete()
        messages.success(request, f"« {livre.titre} » supprimé.")
        return redirect('portail:liste_livres')
    return render(request, 'portail/livres/supprimer.html', {'livre': livre})