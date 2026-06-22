from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings

from .models import Utilisateur, Etudiant, Professeur
from .forms import (
    FormulaireConnexion,
    FormulaireChangementMotDePasse,
    FormulaireUtilisateur,
    FormulaireModificationEtudiant,
    FormulaireModificationProfesseur,
    FormulaireModificationAdministrateur,FormulaireProfilUtilisateur
)
# Ajouter ces imports en haut
import io
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from .badge_generator import generer_badge_pdf

# --------------------------------------------------------------------------
from applications.departements.models import Departement  # 'Department' -> 'Departement' pour matcher la FK 'departements.Departement' de models.py
from applications.cours.models import Cours, SectionCours  # 'Course' -> 'Cours', 'CourseSection' -> 'SectionCours'
from applications.notes.models import Note
from applications.inscriptions.models import Inscription
from utilitaires.roles import est_administrateur
from applications.inscriptions.models import Inscription

statut__in=Inscription.STATUTS_ACTIFS



@login_required
def tableau_bord(request):
    """Tableau de bord personnalisé selon le rôle"""
    utilisateur = request.user
    context = {"utilisateur": utilisateur}

    if utilisateur.est_etudiant():
        etudiant = utilisateur.profil_etudiant

        inscriptions_actives = etudiant.inscriptions.filter(
            statut="INSCRIT"
        ).select_related(
            "section_cours__cours",
            "section_cours__professeur__utilisateur"
        )[:10]

        total_cours      = etudiant.inscriptions.filter(statut="INSCRIT").count()
        cours_completes  = etudiant.inscriptions.filter(statut="COMPLETE").count()

        liste_notes = Note.objects.filter(
            inscription__etudiant=etudiant,
            inscription__statut="COMPLETE",
            note_finale__isnull=False,
        )

        total_points  = 0
        total_credits = 0
        for note in liste_notes:
            credits     = note.inscription.section_cours.cours.credits
            valeur_note = float(note.note_finale)
            if valeur_note >= 90:   points = 4.0
            elif valeur_note >= 80: points = 3.0
            elif valeur_note >= 70: points = 2.0
            elif valeur_note >= 60: points = 1.0
            else:                   points = 0.0
            total_points  += points * credits
            total_credits += credits

        moyenne = round(total_points / total_credits, 2) if total_credits > 0 else 0

        context.update({
            "inscriptions_actives": inscriptions_actives,
            "total_cours":          total_cours,
            "cours_completes":      cours_completes,
            "moyenne":              moyenne,
            "est_etudiant":         True,
        })
        return render(request, "portail/tableau_de_bord_etudiant.html", context)

    elif utilisateur.est_professeur():
        professeur = utilisateur.profil_professeur

        sections = professeur.sections_cours.select_related("cours").annotate(
            nombre_inscrits=Count(
                "inscriptions", filter=Q(inscriptions__statut__in=Inscription.STATUTS_ACTIFS)
            )
        )[:5]

        total_sections = professeur.sections_cours.count()
        total_etudiants_inscrits = Inscription.objects.filter(
            section_cours__professeur=professeur,
            statut__in=Inscription.STATUTS_ACTIFS
        ).count()

        context.update({
            "sections":        sections,
            "total_sections":  total_sections,
            "total_etudiants": total_etudiants_inscrits,
            "est_professeur":  True,
        })
        return render(request, "portail/tableau_de_bord_professeur.html", context)

    elif utilisateur.est_administrateur():
        # ↓ is_active → utilisateur__is_active (champ hérité AbstractUser, reste en anglais)
        total_etudiants   = Etudiant.objects.filter(utilisateur__is_active=True).count()
        total_professeurs = Professeur.objects.filter(utilisateur__is_active=True).count()

        # ↓ is_active → est_actif (champ francisé dans Cours)
        total_cours       = Cours.objects.filter(est_actif=True).count()

        total_inscriptions = Inscription.objects.filter(statut="INSCRIT").count()

        # ⚠️ distinct=True est indispensable ici : deux Count() sur deux relations
        # différentes (etudiants ET professeurs) dans le même annotate() génèrent
        # un JOIN combiné. Sans distinct=True, Count() compte les lignes du
        # produit cartésien des deux JOIN au lieu des objets distincts, ce qui
        # gonfle les totaux et les rend souvent identiques entre les deux colonnes.
        departements = Departement.objects.annotate(
            nombre_etudiants=Count(
                "etudiants",
                filter=Q(etudiants__utilisateur__is_active=True),
                distinct=True,
            ),
            nombre_professeurs=Count(
                "professeurs",
                filter=Q(professeurs__utilisateur__is_active=True),
                distinct=True,
            ),
        )

        # ↓ student → etudiant  |  enrollment_date → date_inscription  |  course_section → section_cours
        inscriptions_recentes = Inscription.objects.select_related(
            "etudiant__utilisateur",
            "section_cours__cours"
        ).order_by("-date_inscription")[:10]

        context.update({
            "total_etudiants":      total_etudiants,
            "total_professeurs":    total_professeurs,
            "total_cours":          total_cours,
            "total_inscriptions":   total_inscriptions,
            "departements":         departements,
            "inscriptions_recentes": inscriptions_recentes,
            "est_admin":            True,
        })
        return render(request, "portail/tableau_de_bord_administrateur.html", context)

    return render(request, "portail/tableau_de_bord_par_defaut.html", context)



def vue_connexion(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect("comptes:tableau_bord")

    if request.method == "POST":
        formulaire = FormulaireConnexion(request.POST)
        if formulaire.is_valid():
            identifiant = formulaire.cleaned_data["identifiant"]  # ← corrigé
            password    = formulaire.cleaned_data["password"]
            utilisateur = authenticate(request, username=identifiant, password=password)

            if utilisateur is not None:
                if utilisateur.is_active:
                    login(request, utilisateur)
                    messages.success(
                        request,
                        f"Bienvenue, {utilisateur.afficher_role_par_genre()} {utilisateur.get_full_name()} !",
                    )
                    if utilisateur.doit_changer_mot_de_passe:
                        return redirect("comptes:changer_mot_de_passe")
                    return redirect("comptes:tableau_bord")
                else:
                    messages.error(request, "Ce compte a été  desactivé par l'administrateur.")
            else:
                messages.error(request, "Identifiant ou mot de passe incorrect.")
    else:
        formulaire = FormulaireConnexion()

    return render(request, "comptes/connexion.html", {"formulaire": formulaire})

def vue_deconnexion(request):
    """Vue de déconnexion avec confirmation"""
    if request.method == "POST":
        logout(request)
        messages.info(request, "Vous avez été déconnecté avec succès.")
        return redirect("accueil")
    return render(request, "comptes/confirmation_deconnexion.html")


@login_required
def vue_changer_mot_de_passe(request):
    """Vue pour changer le mot de passe"""
    utilisateur = request.user

    if request.method == "POST":
        formulaire = FormulaireChangementMotDePasse(utilisateur, request.POST)
        if formulaire.is_valid():
            utilisateur = formulaire.save()
            utilisateur.doit_changer_mot_de_passe = False
            utilisateur.save()
            update_session_auth_hash(request, utilisateur)
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
            return redirect("comptes:tableau_bord")
    else:
        formulaire = FormulaireChangementMotDePasse(utilisateur)

    return render(request, "comptes/changer_mot_de_passe.html", {"formulaire": formulaire})


@login_required
def vue_profil(request):
    """Affichage du profil — modification des infos personnelles uniquement"""
    utilisateur = request.user

    if request.method == "POST":
        form = FormulaireProfilUtilisateur(
            request.POST, request.FILES, instance=utilisateur
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("comptes:profil")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = FormulaireProfilUtilisateur(instance=utilisateur)

    context = {
        "utilisateur": utilisateur,
        "form": form,
    }

    if utilisateur.est_administrateur():
        try:
            context["administrateur"] = utilisateur.profil_admin
        except Exception:
            context["administrateur"] = None

    elif utilisateur.est_etudiant():
        try:
            context["etudiant"] = utilisateur.profil_etudiant
        except Exception:
            context["etudiant"] = None

    elif utilisateur.est_professeur():
        try:
            context["professeur"] = utilisateur.profil_professeur
        except Exception:
            context["professeur"] = None

    return render(request, "comptes/profil.html", context)



@login_required
@user_passes_test(est_administrateur)
def vue_liste_utilisateurs(request):
    """Liste des utilisateurs (admin uniquement)"""
    utilisateurs = Utilisateur.objects.all().order_by("-cree_le")

    role = request.GET.get("role", "").strip()
    recherche = request.GET.get("search", "").strip()

    if role:
        utilisateurs = utilisateurs.filter(role=role)

    if recherche:
        q_recherche = (
            Q(email__icontains=recherche)
            | Q(first_name__icontains=recherche)
            | Q(last_name__icontains=recherche)
        )
        parties = recherche.split()
        if len(parties) == 2:
            q_recherche |= (
                Q(first_name__icontains=parties[0], last_name__icontains=parties[1])
                | Q(first_name__icontains=parties[1], last_name__icontains=parties[0])
            )
        utilisateurs = utilisateurs.filter(q_recherche)

    paginator = Paginator(utilisateurs, getattr(settings, "ELEMENTS_PAR_PAGE", 10))
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "role_choices": Utilisateur.CHOIX_ROLE,
        "current_role": role,
        "recherche": recherche,
    }

    return render(request, "comptes/liste_utilisateurs.html", context)  # ← ne doit pas être dans un bloc if


@login_required
@user_passes_test(est_administrateur)
def vue_creer_utilisateur(request):
    if request.method == 'POST':
        formulaire = FormulaireUtilisateur(request.POST, request.FILES)
        if formulaire.is_valid():
            utilisateur = formulaire.save(commit=False)
            mot_de_passe_temporaire = getattr(settings, 'MOT_DE_PASSE_TEMPORAIRE', 'motdepasse123')
            utilisateur.set_password(mot_de_passe_temporaire)
            utilisateur.doit_changer_mot_de_passe = True
            utilisateur.save()
            messages.success(
                request,
                f"Utilisateur {utilisateur.get_full_name()} créé. "
                f"Mot de passe temporaire : {mot_de_passe_temporaire}"
            )
            return redirect('comptes:liste_utilisateurs')
        else:
            messages.error(request, "Le formulaire contient des erreurs.")
    else:
        formulaire = FormulaireUtilisateur()

    return render(request, 'comptes/formulaire_utilisateur.html', {
        'formulaire': formulaire,
        'titre': "Créer un utilisateur",
        'bouton': "Créer",
    })


from .forms import (
    FormulaireUtilisateur,
    FormulaireProfilEtudiant,       # ← nouveau
    FormulaireModificationProfesseur,
    FormulaireModificationAdministrateur,
)

@login_required
@user_passes_test(est_administrateur)
def vue_modifier_utilisateur(request, utilisateur_id):
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    formulaire_profil = None

    if request.method == 'POST':
        formulaire = FormulaireUtilisateur(request.POST, request.FILES, instance=utilisateur)

        # Instancier le formulaire profil AVANT la validation
        if utilisateur.est_etudiant():
            formulaire_profil = FormulaireProfilEtudiant(          # ← changement clé
                request.POST, instance=utilisateur.profil_etudiant)
        elif utilisateur.est_professeur():
            formulaire_profil = FormulaireModificationProfesseur(
                request.POST, instance=utilisateur.profil_professeur)
        elif utilisateur.est_administrateur() and hasattr(utilisateur, 'profil_admin'):
            formulaire_profil = FormulaireModificationAdministrateur(
                request.POST, instance=utilisateur.profil_admin)

        formulaire_valide = formulaire.is_valid()
        profil_valide = formulaire_profil.is_valid() if formulaire_profil else True

        if formulaire_valide and profil_valide:
            formulaire.save()
            if formulaire_profil:
                formulaire_profil.save()
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect('comptes:liste_utilisateurs')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        formulaire = FormulaireUtilisateur(instance=utilisateur)

        if utilisateur.est_etudiant():
            formulaire_profil = FormulaireProfilEtudiant(          # ← changement clé
                instance=utilisateur.profil_etudiant)
        elif utilisateur.est_professeur():
            formulaire_profil = FormulaireModificationProfesseur(
                instance=utilisateur.profil_professeur)
        elif utilisateur.est_administrateur() and hasattr(utilisateur, 'profil_admin'):
            formulaire_profil = FormulaireModificationAdministrateur(
                instance=utilisateur.profil_admin)

    return render(request, 'comptes/formulaire_utilisateur.html', {
        'formulaire': formulaire,
        'formulaire_profil': formulaire_profil,
        'utilisateur_obj': utilisateur,
        'titre': f"Modifier — {utilisateur.get_full_name()}",
        'bouton': "Enregistrer",
    })


@login_required
@user_passes_test(est_administrateur)
def vue_basculer_actif(request, utilisateur_id):
    """Activer/désactiver un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save()

    statut = "activé" if utilisateur.is_active else "désactivé"
    messages.success(request, f"Utilisateur {utilisateur.get_full_name()} {statut}.")

    return redirect("comptes:liste_utilisateurs")


@login_required
@user_passes_test(est_administrateur)
def vue_reinitialiser_mot_de_passe(request, utilisateur_id):
    """Réinitialiser le mot de passe d'un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    mot_de_passe_temporaire = getattr(settings, "MOT_DE_PASSE_TEMPORAIRE", "motdepasse123")
    utilisateur.set_password(mot_de_passe_temporaire)
    utilisateur.doit_changer_mot_de_passe = True
    utilisateur.save()

    messages.success(
        request,
        f"Mot de passe réinitialisé pour {utilisateur.get_full_name()}. "
        f"Nouveau mot de passe temporaire : {mot_de_passe_temporaire}",
    )

    return redirect("comptes:liste_utilisateurs")


# === Liste des professeurs ===
@login_required
@user_passes_test(est_administrateur)
def vue_liste_professeurs(request):
    """Liste de tous les professeurs"""
    professeurs = Utilisateur.objects.filter(role="PROFESSEUR").select_related(
        "profil_professeur", "profil_professeur__departement"
    ).order_by("last_name", "first_name")

    recherche = request.GET.get("search")
    if recherche:
        professeurs = professeurs.filter(
            Q(first_name__icontains=recherche)
            | Q(last_name__icontains=recherche)
            | Q(email__icontains=recherche)
            | Q(profil_professeur__identifiant_professeur__icontains=recherche)
        )

    departement_filtre = request.GET.get("departement")
    if departement_filtre:
        professeurs = professeurs.filter(profil_professeur__departement__code=departement_filtre)

    specialite_filtre = request.GET.get("specialite")
    if specialite_filtre:
        professeurs = professeurs.filter(profil_professeur__specialite=specialite_filtre)

    statut_filtre = request.GET.get("statut")
    if statut_filtre == "actif":
        professeurs = professeurs.filter(is_active=True)
    elif statut_filtre == "inactif":
        professeurs = professeurs.filter(is_active=False)

    paginator = Paginator(professeurs, getattr(settings, "ELEMENTS_PAR_PAGE", 10))
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    specialites = (
        Professeur.objects.exclude(specialite="")
        .order_by("specialite")
        .values_list("specialite", flat=True)
        .distinct()
    )

    return render(
        request,
        "portail/liste_professeurs.html",
        {
            "page_obj": page_obj,
            "recherche": recherche,
            "departements": Departement.objects.all().order_by("nom"),
            "specialites": specialites,
            "departement_filtre": departement_filtre,
            "specialite_filtre": specialite_filtre,
            "statut_filtre": statut_filtre,
        },
    )

@login_required
@user_passes_test(est_administrateur)
def vue_detail_professeur(request, pk):
    """Détail d'un profil professeur"""

    professeur = get_object_or_404(
        Professeur.objects.select_related(
            "utilisateur",
            "departement",
        ),
        pk=pk,
    )

    return render(
        request,
        "portail/detail_professeur.html",
        {
            "professeur": professeur,
        },
    )
    
    
# === Liste des étudiants ===
# === Liste des étudiants ===
@login_required
@user_passes_test(est_administrateur)
def vue_liste_etudiants(request):
    """Liste de tous les étudiants"""
    etudiants = Utilisateur.objects.filter(role="ETUDIANT").select_related(
        "profil_etudiant", "profil_etudiant__departement"
    ).order_by("last_name", "first_name")

    recherche = request.GET.get("search")
    if recherche:
        etudiants = etudiants.filter(
            Q(first_name__icontains=recherche)
            | Q(last_name__icontains=recherche)
            | Q(profil_etudiant__numero_etudiant__icontains=recherche)
            | Q(email__icontains=recherche)
        )

    departement_filtre = request.GET.get("departement")
    if departement_filtre:
        etudiants = etudiants.filter(profil_etudiant__departement__code=departement_filtre)

    niveau_filtre = request.GET.get("niveau")
    if niveau_filtre:
        etudiants = etudiants.filter(profil_etudiant__niveau=niveau_filtre)

    paginator = Paginator(etudiants, getattr(settings, "ELEMENTS_PAR_PAGE", 10))
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "portail/liste_etudiants.html",
        {
            "page_obj": page_obj,
            "recherche": recherche,
            "departements": Departement.objects.all().order_by("nom"),
            "niveaux": Etudiant.CHOIX_ANNEE,
            "departement_filtre": departement_filtre,
            "niveau_filtre": niveau_filtre,
        },
    )



@login_required
def vue_detail_etudiant(request, pk):
    """Détail d'un profil étudiant — modification réservée à l'admin"""
    utilisateur = request.user

    # Seuls les admins et les profs peuvent accéder à cette page
    if not (utilisateur.est_administrateur() or utilisateur.est_professeur()):
        messages.error(request, "Accès non autorisé.")
        return redirect("portail:tableau_bord")

    etudiant = get_object_or_404(
        Etudiant.objects.select_related("utilisateur", "departement"),
        pk=pk,
    )

    peut_modifier = utilisateur.est_administrateur()

    form = FormulaireModificationEtudiant(
        request.POST or None, instance=etudiant
    ) if peut_modifier else None

    if request.method == "POST":
        if not peut_modifier:
            messages.error(request, "Vous n'avez pas la permission de modifier ce profil.")
            return redirect("comptes:detail_etudiant", pk=pk)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil étudiant mis à jour avec succès.")
            return redirect("comptes:detail_etudiant", pk=pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")

    return render(request, "portail/detail_etudiant.html", {
        "etudiant": etudiant,
        "form": form,
        "peut_modifier": peut_modifier,
    })




# ── Vue téléchargement PDF ───────────────────────────────────────────────────
@login_required
def badge_pdf(request):
    etudiant = getattr(request.user, 'profil_etudiant', None)
    if etudiant is None:
        messages.error(request, "Badge disponible uniquement pour les étudiants.")
        return redirect('comptes:profil')

    pdf_bytes = generer_badge_pdf(etudiant)
    response  = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="badge_{etudiant.numero_etudiant}.pdf"'
    )
    return response

# ── Vue téléchargement PNG ───────────────────────────────────────────────────
@login_required
def badge_png(request):
    etudiant = getattr(request.user, 'profil_etudiant', None)
    if etudiant is None:
        messages.error(request, "Badge disponible uniquement pour les étudiants.")
        return redirect('comptes:profil')

    pdf_bytes = generer_badge_pdf(etudiant)

    from pdf2image import convert_from_bytes
    images = convert_from_bytes(pdf_bytes, dpi=300)
    buf    = io.BytesIO()
    images[0].save(buf, format='PNG', optimize=True)
    buf.seek(0)

    response = HttpResponse(buf.read(), content_type='image/png')
    response['Content-Disposition'] = (
        f'attachment; filename="badge_{etudiant.numero_etudiant}.png"'
    )
    return response