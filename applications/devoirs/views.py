import os
import zipfile
import io

from django.shortcuts       import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib         import messages
from django.utils           import timezone
from django.http            import HttpResponse, Http404
from django.db.models       import Count, Q

from applications.cours.models   import SectionCours
from .models  import Devoir, FichierDevoir, Remise, FichierRemise
from .forms   import (
    FormulaireDevoir, FormulaireFichierDevoir,
    FormulaireMultiFichiersDevoir,
    FormulaireRemise, FormulaireFichiersRemise,
    FormulaireNote,
)
from utilitaires.roles import est_administrateur, est_etudiant, est_professeur


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES INTERNES
# ═══════════════════════════════════════════════════════════════════════════════

def _verifier_proprietaire_devoir(request, devoir):
    """Lève Http404 si le prof connecté n'est pas le créateur du devoir
    et qu'il n'est pas administrateur."""
    if request.user.role != 'ADMINISTRATEUR' and devoir.cree_par != request.user:
        raise Http404("Devoir introuvable.")


def _verifier_inscription_etudiant(request, devoir):
    """Redirige si l'étudiant n'est pas inscrit à la section du devoir."""
    etudiant = request.user.profil_etudiant
    inscrit  = etudiant.inscriptions.filter(
        section_cours=devoir.section_cours,
        statut__in=['INSCRIT', 'COMPLETE'],
    ).exists()
    if not inscrit:
        messages.error(request, "Vous n'êtes pas inscrit à ce cours.")
        return False
    return True


def _sauvegarder_fichiers_devoir(request, devoir):
    """Enregistre tous les fichiers postés pour un devoir."""
    fichiers_postes = request.FILES.getlist('fichiers')
    for f in fichiers_postes:
        nom = request.POST.get('nom_fichier', '') or f.name
        FichierDevoir.objects.create(devoir=devoir, fichier=f, nom=nom or f.name)


def _sauvegarder_fichiers_remise(request, remise):
    """Enregistre tous les fichiers postés pour une remise."""
    fichiers_postes = request.FILES.getlist('fichiers')
    for f in fichiers_postes:
        FichierRemise.objects.create(remise=remise, fichier=f, nom=f.name)


# ═══════════════════════════════════════════════════════════════════════════════
# VUES PROFESSEUR
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(est_professeur)
def liste_devoirs_prof(request):
    """Liste de tous les devoirs créés par le professeur connecté."""
    if request.user.role == 'ADMINISTRATEUR':
        devoirs      = Devoir.objects.select_related('section_cours__cours').order_by('-cree_le')
        mes_sections = SectionCours.objects.select_related('cours').order_by('cours__code')
    else:
        devoirs      = Devoir.objects.filter(
            cree_par=request.user
        ).select_related('section_cours__cours').order_by('-cree_le')
        mes_sections = SectionCours.objects.filter(
            professeur=request.user.profil_professeur
        ).select_related('cours').order_by('cours__code')

    # Annoter avec le nombre de remises
    devoirs = devoirs.annotate(
        nb_remises=Count('remises'),
        nb_notes=Count('remises', filter=Q(remises__statut='NOTE')),
    )

    # Filtres GET
    filtre_publie = request.GET.get('publie', '')
    filtre_section = request.GET.get('section', '')

    if filtre_publie == '1':
        devoirs = devoirs.filter(est_publie=True)
    elif filtre_publie == '0':
        devoirs = devoirs.filter(est_publie=False)

    if filtre_section:
        devoirs = devoirs.filter(section_cours_id=filtre_section)

    return render(request, 'devoirs/liste_devoirs.html', {
        'devoirs':        devoirs,
        'mes_sections':   mes_sections,
        'filtre_publie':  filtre_publie,
        'filtre_section': filtre_section,
    })


@login_required
@user_passes_test(est_professeur)
def creer_devoir(request, section_id):
    """Créer un nouveau devoir pour une section donnée."""
    section = get_object_or_404(SectionCours, id=section_id)

    formulaire       = FormulaireDevoir(request.POST or None)
    form_fichiers    = FormulaireMultiFichiersDevoir(request.POST or None, request.FILES or None)

    if request.method == 'POST' and formulaire.is_valid() and form_fichiers.is_valid():
        devoir               = formulaire.save(commit=False)
        devoir.section_cours = section
        devoir.cree_par      = request.user
        devoir.save()

        _sauvegarder_fichiers_devoir(request, devoir)

        messages.success(request, f"Devoir « {devoir.titre} » créé avec succès.")
        return redirect('devoirs:detail_devoir', devoir_id=devoir.id)

    return render(request, 'devoirs/formulaire_devoir.html', {
        'formulaire':    formulaire,
        'form_fichiers': form_fichiers,
        'section':       section,
        'titre':         f"Créer un devoir — {section.cours.code}",
        'mode':          'creation',
    })


@login_required
@user_passes_test(est_professeur)
def detail_devoir(request, devoir_id):
    """Détail d'un devoir + statistiques des remises (vue professeur)."""
    devoir = get_object_or_404(
        Devoir.objects.select_related('section_cours__cours', 'cree_par'),
        id=devoir_id,
    )
    _verifier_proprietaire_devoir(request, devoir)

    remises    = devoir.remises.select_related('etudiant__utilisateur').prefetch_related('fichiers').order_by('-remis_le')
    nb_remises = remises.count()
    nb_notes   = remises.filter(statut='NOTE').count()
    nb_retard  = remises.filter(statut='EN_RETARD').count()

    return render(request, 'devoirs/detail_devoir.html', {
        'devoir':     devoir,
        'remises':    remises[:5],
        'nb_remises': nb_remises,
        'nb_notes':   nb_notes,
        'nb_retard':  nb_retard,
    })


@login_required
@user_passes_test(est_professeur)
def modifier_devoir(request, devoir_id):
    """Modifier un devoir existant (infos + fichiers joints)."""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    _verifier_proprietaire_devoir(request, devoir)

    formulaire    = FormulaireDevoir(request.POST or None, instance=devoir)
    form_fichiers = FormulaireMultiFichiersDevoir(request.POST or None, request.FILES or None)

    if request.method == 'POST' and formulaire.is_valid() and form_fichiers.is_valid():
        formulaire.save()
        _sauvegarder_fichiers_devoir(request, devoir)

        # Supprimer les fichiers cochés pour suppression
        ids_a_supprimer = request.POST.getlist('supprimer_fichier')
        if ids_a_supprimer:
            FichierDevoir.objects.filter(id__in=ids_a_supprimer, devoir=devoir).delete()

        messages.success(request, "Devoir modifié avec succès.")
        return redirect('devoirs:detail_devoir', devoir_id=devoir.id)

    return render(request, 'devoirs/formulaire_devoir.html', {
        'formulaire':    formulaire,
        'form_fichiers': form_fichiers,
        'section':       devoir.section_cours,
        'devoir':        devoir,
        'titre':         f"Modifier — {devoir.titre}",
        'mode':          'modification',
        'fichiers_existants': devoir.fichiers.all(),
    })


@login_required
@user_passes_test(est_professeur)
def supprimer_devoir(request, devoir_id):
    """Supprimer un devoir (avec page de confirmation)."""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    _verifier_proprietaire_devoir(request, devoir)

    if request.method == 'POST':
        titre = devoir.titre
        devoir.delete()
        messages.success(request, f"Devoir « {titre} » supprimé.")
        return redirect('devoirs:liste_devoirs')

    return render(request, 'devoirs/supprimer_devoir.html', {'devoir': devoir})


@login_required
@user_passes_test(est_professeur)
def basculer_publication(request, devoir_id):
    """Publier ou masquer un devoir (toggle via POST)."""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    if not _verifier_proprietaire_devoir(request, devoir):
        return redirect('devoirs:liste_devoirs')

    if request.method == 'POST':
        devoir.est_publie = not devoir.est_publie
        devoir.save(update_fields=['est_publie'])
        etat = "publié" if devoir.est_publie else "masqué"
        messages.success(request, f"Devoir « {devoir.titre} » {etat}.")

    # Redirection propre : next doit être un chemin absolu (/devoirs/2/),
    # sinon on retombe sur le détail du devoir
    next_url = request.POST.get('next', '')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('devoirs:detail_devoir', devoir_id=devoir.id)


@login_required
@user_passes_test(est_professeur)
def supprimer_fichier_devoir(request, fichier_id):
    """Supprimer un fichier joint à un devoir."""
    fichier = get_object_or_404(FichierDevoir, id=fichier_id)
    devoir  = fichier.devoir
    _verifier_proprietaire_devoir(request, devoir)

    if request.method == 'POST':
        fichier.delete()
        messages.success(request, "Fichier supprimé.")

    return redirect('devoirs:modifier_devoir', devoir_id=devoir.id)


@login_required
@user_passes_test(est_professeur)
def liste_remises(request, devoir_id):
    """Toutes les remises d'un devoir, avec filtres et aperçu."""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    _verifier_proprietaire_devoir(request, devoir)

    statut  = request.GET.get('statut', '')
    remises = devoir.remises.select_related('etudiant__utilisateur').prefetch_related('fichiers').order_by('-remis_le')

    if statut:
        remises = remises.filter(statut=statut)

    return render(request, 'devoirs/liste_remises.html', {
        'devoir':        devoir,
        'remises':       remises,
        'statut_choisi': statut,
        'choix_statut':  Remise.CHOIX_STATUT,
        'nb_total':      devoir.remises.count(),
    })


@login_required
@user_passes_test(est_professeur)
def noter_remise(request, remise_id):
    """Attribuer une note et un commentaire à une remise."""
    remise = get_object_or_404(
        Remise.objects.select_related('devoir', 'etudiant__utilisateur').prefetch_related('fichiers'),
        id=remise_id,
    )
    _verifier_proprietaire_devoir(request, remise.devoir)

    formulaire = FormulaireNote(
        request.POST or None,
        instance=remise,
        points_max=remise.devoir.points_max,
    )

    if request.method == 'POST' and formulaire.is_valid():
        remise        = formulaire.save(commit=False)
        remise.statut = 'NOTE'
        remise.save()
        messages.success(
            request,
            f"Note enregistrée pour {remise.etudiant.utilisateur.get_full_name()}."
        )
        return redirect('devoirs:liste_remises', devoir_id=remise.devoir.id)

    return render(request, 'devoirs/noter_remise.html', {
        'formulaire': formulaire,
        'remise':     remise,
        'devoir':     remise.devoir,
    })


@login_required
@user_passes_test(est_professeur)
def telecharger_remises(request, devoir_id):
    """Télécharger toutes les remises d'un devoir en une archive ZIP."""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    _verifier_proprietaire_devoir(request, devoir)

    remises = devoir.remises.select_related('etudiant__utilisateur').prefetch_related('fichiers')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for remise in remises:
            nom_etudiant = remise.etudiant.utilisateur.get_full_name().replace(' ', '_')
            # Fichiers soumis
            for fich in remise.fichiers.all():
                try:
                    chemin_dans_zip = f"{nom_etudiant}/{os.path.basename(fich.fichier.name)}"
                    zf.writestr(chemin_dans_zip, fich.fichier.read())
                except Exception:
                    pass
            # Réponse texte
            if remise.contenu:
                zf.writestr(
                    f"{nom_etudiant}/reponse.txt",
                    remise.contenu.encode('utf-8'),
                )

    buffer.seek(0)
    nom_zip = f"remises_{devoir.titre[:30].replace(' ', '_')}.zip"
    reponse = HttpResponse(buffer.read(), content_type='application/zip')
    reponse['Content-Disposition'] = f'attachment; filename="{nom_zip}"'
    return reponse


# ═══════════════════════════════════════════════════════════════════════════════
# VUES ÉTUDIANT
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(est_etudiant)
def mes_devoirs(request):
    """Tous les devoirs publiés des sections où l'étudiant est inscrit."""
    etudiant     = request.user.profil_etudiant
    inscriptions = etudiant.inscriptions.filter(
        statut__in=['INSCRIT', 'COMPLETE']
    ).values_list('section_cours_id', flat=True)

    maintenant = timezone.now()

    devoirs = Devoir.objects.filter(
        section_cours_id__in=inscriptions,
        est_publie=True,
    ).filter(
        Q(date_publication__isnull=True) | Q(date_publication__lte=maintenant)
    ).select_related('section_cours__cours').order_by('date_limite')

    # Filtres
    filtre = request.GET.get('filtre', 'tous')

    # Annoter chaque devoir avec la remise de l'étudiant
    for devoir in devoirs:
        try:
            devoir.ma_remise = devoir.remises.get(etudiant=etudiant)
        except Remise.DoesNotExist:
            devoir.ma_remise = None
        devoir.en_retard = devoir.est_en_retard()

    # Appliquer le filtre côté Python (pour éviter une nouvelle requête)
    if filtre == 'a_remettre':
        devoirs = [d for d in devoirs if not d.ma_remise and not d.en_retard]
    elif filtre == 'remis':
        devoirs = [d for d in devoirs if d.ma_remise]
    elif filtre == 'retard':
        devoirs = [d for d in devoirs if d.en_retard and not d.ma_remise]
    elif filtre == 'note':
        devoirs = [d for d in devoirs if d.ma_remise and d.ma_remise.statut == 'NOTE']

    filtres_disponibles = [
        ('tous',       'Tous',             'list-ul'),
        ('a_remettre', 'À remettre',       'hourglass-half'),
        ('remis',      'Remis',            'paper-plane'),
        ('retard',     'En retard',        'clock'),
        ('note',       'Notés',            'star'),
    ]

    return render(request, 'devoirs/mes_devoirs.html', {
        'devoirs':            devoirs,
        'filtre':             filtre,
        'filtres_disponibles': filtres_disponibles,
    })


@login_required
@user_passes_test(est_etudiant)
def detail_devoir_etudiant(request, devoir_id):
    """Vue détaillée d'un devoir côté étudiant."""
    devoir   = get_object_or_404(Devoir, id=devoir_id, est_publie=True)
    etudiant = request.user.profil_etudiant

    if not _verifier_inscription_etudiant(request, devoir):
        return redirect('devoirs:mes_devoirs')

    remise_existante = Remise.objects.filter(
        devoir=devoir, etudiant=etudiant
    ).prefetch_related('fichiers').first()

    return render(request, 'devoirs/detail_devoir_etudiant.html', {
        'devoir':           devoir,
        'remise_existante': remise_existante,
        'en_retard':        devoir.est_en_retard(),
    })


@login_required
@user_passes_test(est_etudiant)
def remettre_devoir(request, devoir_id):
    """Soumettre ou modifier une remise pour un devoir."""
    devoir   = get_object_or_404(Devoir, id=devoir_id, est_publie=True)
    etudiant = request.user.profil_etudiant

    if not _verifier_inscription_etudiant(request, devoir):
        return redirect('devoirs:mes_devoirs')

    remise_existante = Remise.objects.filter(
        devoir=devoir, etudiant=etudiant
    ).prefetch_related('fichiers').first()
    
    # Bloquer la modification si la remise est déjà notée
    if remise_existante and remise_existante.statut == 'NOTE':
        messages.warning(request, "Ce devoir a déjà été noté. Vous ne pouvez plus modifier votre remise.")
        return redirect('devoirs:detail_devoir_etudiant', devoir_id=devoir.id)

    # Bloquer la création d'une NOUVELLE remise après la date limite
    if devoir.est_en_retard() and not remise_existante:
        messages.error(request, "Le délai de remise est expiré. Vous ne pouvez plus soumettre ce devoir.")
        return redirect('devoirs:mes_devoirs')

    # Bloquer la modification après la date limite
    if devoir.est_en_retard() and remise_existante:
        messages.warning(request, "Le délai est expiré. Votre remise est verrouillée.")
        return redirect('devoirs:detail_devoir_etudiant', devoir_id=devoir.id)

    formulaire      = FormulaireRemise(
        request.POST or None,
        instance=remise_existante,
        type_devoir=devoir.type_devoir,
    )
    form_fichiers   = FormulaireFichiersRemise(request.POST or None, request.FILES or None)

    if request.method == 'POST' and formulaire.is_valid() and form_fichiers.is_valid():
        remise          = formulaire.save(commit=False)
        remise.devoir   = devoir
        remise.etudiant = etudiant
        remise.statut   = 'EN_RETARD' if devoir.est_en_retard() else 'RENDU'
        remise.save()

        # Ajouter les nouveaux fichiers
        _sauvegarder_fichiers_remise(request, remise)

        # Supprimer les fichiers cochés pour suppression
        ids_a_supprimer = request.POST.getlist('supprimer_fichier')
        if ids_a_supprimer:
            FichierRemise.objects.filter(id__in=ids_a_supprimer, remise=remise).delete()

        messages.success(request, "Votre travail a été remis avec succès.")
        return redirect('devoirs:mes_devoirs')

    return render(request, 'devoirs/remettre_devoir.html', {
        'formulaire':       formulaire,
        'form_fichiers':    form_fichiers,
        'devoir':           devoir,
        'remise_existante': remise_existante,
    })
