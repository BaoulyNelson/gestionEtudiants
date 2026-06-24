from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings

from applications.inscriptions.models import Inscription

from .models import Cours, SectionCours
from .forms import FormulaireCours, FormulaireSection
from applications.comptes.views import est_administrateur

# ===========================================================================
# COURS
# ===========================================================================


@login_required
def liste_cours(request):
    """Affiche la liste paginée des cours actifs avec filtres"""
    cours = Cours.objects.filter(est_actif=True).select_related("departement")

    departement = request.GET.get("departement")
    niveau = request.GET.get("niveau")
    recherche = request.GET.get("recherche")

    if niveau:
        cours = cours.filter(niveau=niveau)
        if niveau == "PREPARATOIRE":
            cours = cours.filter(departement__isnull=True)
        elif departement:
            cours = cours.filter(departement__code=departement)
    elif departement:
        cours = cours.filter(departement__code=departement)

    if recherche:
        cours = cours.filter(Q(code__icontains=recherche) | Q(nom__icontains=recherche))

    paginateur = Paginator(cours, settings.ELEMENTS_PAR_PAGE)
    numero_page = request.GET.get("page")
    page = paginateur.get_page(numero_page)

    from applications.departements.models import Departement

    contexte = {
        "page_obj": page,
        "departements": Departement.objects.all(),
        "choix_annee": Cours.CHOIX_ANNEE,
        "departement_actuel": departement,
        "niveau_actuel": niveau,
        "recherche": recherche,
    }
    return render(request, "cours/liste_cours.html", contexte)


@login_required
def detail_cours(request, id_cours):
    cours = get_object_or_404(Cours, id=id_cours)
    sections = (
        cours.sections
        .select_related("professeur__utilisateur")
        .annotate(
            nb_inscrits=Count(
                "inscriptions",
                filter=Q(inscriptions__statut__in=["INSCRIT", "COMPLETE", "ECHOUE"])
            )
        )
        .order_by("numero_section")
    )

    if request.user.est_etudiant():
        etudiant = request.user.profil_etudiant
        inscrites = sections.filter(
            inscriptions__etudiant=etudiant,
            inscriptions__statut__in=["INSCRIT", "COMPLETE", "ECHOUE"],
        )
        sections = inscrites if inscrites.exists() else sections

    contexte = {
        "cours": cours,
        "sections": sections,
    }
    return render(request, "cours/detail_cours.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def creer_cours(request):
    """Crée un nouveau cours"""
    if request.method == "POST":
        formulaire = FormulaireCours(request.POST)
        if formulaire.is_valid():
            cours = formulaire.save()
            messages.success(request, f"Cours {cours.code} créé avec succès.")
            return redirect("cours:liste_cours")
    else:
        formulaire = FormulaireCours()

    return render(request, "cours/formulaire_cours.html", {"formulaire": formulaire})


@login_required
@user_passes_test(est_administrateur)
def modifier_cours(request, id_cours):
    """Modifie un cours existant"""
    cours = get_object_or_404(Cours, id=id_cours)

    if request.method == "POST":
        formulaire = FormulaireCours(request.POST, instance=cours)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, "Cours modifié avec succès.")
            return redirect("cours:detail_cours", id_cours=cours.id)
    else:
        formulaire = FormulaireCours(instance=cours)

    return render(
        request,
        "cours/formulaire_cours.html",
        {"formulaire": formulaire, "cours": cours},
    )


@login_required
@user_passes_test(est_administrateur)
def desactiver_cours(request, id_cours):
    """Désactive un cours (suppression douce)"""
    cours = get_object_or_404(Cours, id=id_cours)
    cours.est_actif = False
    cours.save()
    messages.success(request, f"Cours {cours.code} désactivé.")
    return redirect("cours:liste_cours")


# ===========================================================================
# SECTIONS DE COURS
# ===========================================================================


@login_required
def liste_sections(request):
    """Affiche la liste paginée des sections avec filtres"""
    sections = SectionCours.objects.select_related(
        "cours", "professeur__utilisateur"
    ).annotate(
        nb_inscrits=Count(
            "inscriptions",
            filter=Q(inscriptions__statut__in=Inscription.STATUTS_ACTIFS)  # ✅ INSCRIT + COMPLETE
        )
    )

    session = request.GET.get("session")
    semestre = request.GET.get("semestre")
    annee = request.GET.get("annee")
    professeur = request.GET.get("professeur")

    if session:
        sections = sections.filter(session=session)
    if semestre:
        sections = sections.filter(semestre=semestre)
    if annee:
        sections = sections.filter(annee=annee)
    if professeur:
        sections = sections.filter(professeur_id=professeur)

    if request.user.est_professeur():
        sections = sections.filter(professeur=request.user.profil_professeur)

    sections = sections.order_by(
        "annee", "semestre", "session", "cours__code", "numero_section"
    )

    paginateur = Paginator(sections, settings.ELEMENTS_PAR_PAGE)
    numero_page = request.GET.get("page")
    page = paginateur.get_page(numero_page)

    contexte = {
        "page_obj": page,
        "choix_session": SectionCours.CHOIX_SESSION,
        "choix_semestre": SectionCours.CHOIX_SEMESTRE,
    }
    return render(request, "cours/liste_sections.html", contexte)

@login_required
def detail_section(request, id_section):
    """Affiche le détail d'une section et la liste de ses inscrits"""
    section = get_object_or_404(
        SectionCours.objects.select_related("cours", "professeur__utilisateur"),
        id=id_section,
    )



    inscriptions = section.inscriptions.filter(
    statut__in=Inscription.STATUTS_ACTIFS
)
    nb_inscrits = inscriptions.count()
    capacite_max = getattr(section, "capacite_max", 0) or 0
    taux_remplissage = int((nb_inscrits / capacite_max) * 100) if capacite_max else 0
    places_disponibles = max(capacite_max - nb_inscrits, 0)
    est_pleine = capacite_max > 0 and nb_inscrits >= capacite_max

    peut_voir_inscrits = request.user.est_administrateur() or (
        request.user.est_professeur()
        and section.professeur == request.user.profil_professeur
    )

    contexte = {
        "section": section,
        "inscriptions": inscriptions if peut_voir_inscrits else None,
        "peut_voir_inscrits": peut_voir_inscrits,
        "nb_inscrits": nb_inscrits,
        "taux_remplissage": taux_remplissage,
        "places_disponibles": places_disponibles,
        "est_pleine": est_pleine,
    }
    return render(request, "cours/detail_section.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def creer_section(request, id_cours=None):
    """Crée une nouvelle section, éventuellement pré-associée à un cours"""
    cours = get_object_or_404(Cours, id=id_cours) if id_cours else None

    if request.method == "POST":
        formulaire = FormulaireSection(request.POST)
        if formulaire.is_valid():
            section = formulaire.save()
            messages.success(
                request,
                f"Section {section.cours.code}-{section.numero_section} créée.",
            )
            return redirect("cours:detail_section", id_section=section.id)
    else:
        valeurs_initiales = {"cours": cours} if cours else {}
        formulaire = FormulaireSection(initial=valeurs_initiales)

    return render(
        request,
        "cours/formulaire_section.html",
        {"formulaire": formulaire, "cours": cours},
    )


@login_required
@user_passes_test(est_administrateur)
def modifier_section(request, id_section):
    """Modifie une section existante"""
    section = get_object_or_404(SectionCours, id=id_section)

    if request.method == "POST":
        formulaire = FormulaireSection(request.POST, instance=section)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, "Section modifiée avec succès.")
            return redirect("cours:detail_section", id_section=section.id)
    else:
        formulaire = FormulaireSection(instance=section)

    return render(
        request,
        "cours/formulaire_section.html",
        {"formulaire": formulaire, "section": section},
    )


@login_required
@user_passes_test(est_administrateur)
def supprimer_section(request, pk):
    """Supprime définitivement une section (admin uniquement)"""
    section = get_object_or_404(SectionCours, pk=pk)

    if request.method == "POST":
        libelle = str(section)
        id_cours = section.cours.id
        section.delete()
        messages.success(request, f"La section {libelle} a été supprimée.")
        return redirect("cours:detail_cours", id_cours=id_cours)

    return render(
        request,
        "cours/confirmer_suppression_section.html",
        {"section": section},
    )


@login_required
@user_passes_test(est_administrateur)
def basculer_ouverture_section(request, id_section):
    """Ouvre ou ferme une section aux inscriptions"""
    section = get_object_or_404(SectionCours, id=id_section)
    section.est_ouverte = not section.est_ouverte
    section.save()

    etat = "ouverte" if section.est_ouverte else "fermée"
    messages.success(request, f"Section {etat} aux inscriptions.")
    return redirect("cours:detail_section", id_section=section.id)

import csv
from django.http import HttpResponse

@login_required
@user_passes_test(est_administrateur)
def vue_export_section_csv(request, section_id):
    section = get_object_or_404(
        SectionCours.objects.select_related("cours"), id=section_id
    )
    inscriptions = (
        section.inscriptions
        .filter(statut__in=["INSCRIT", "COMPLETE", "ECHOUE"])
        .select_related("etudiant__utilisateur", "etudiant__departement")
        .order_by("etudiant__utilisateur__last_name")
    )

    nom_fichier = f"section_{section.cours.code}_{section.numero_section}.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'

    writer = csv.writer(response)
    writer.writerow(["Numéro", "Nom", "Prénom", "Email", "Département", "Niveau", "Statut"])
    for ins in inscriptions:
        e = ins.etudiant
        u = e.utilisateur
        writer.writerow([
            e.numero_etudiant,
            u.last_name,
            u.first_name,
            u.email,
            e.departement.nom if e.departement else "—",
            e.get_niveau_display(),
            ins.get_statut_display(),
        ])

    return response
# ===========================================================================
# MES COURS
# ===========================================================================


@login_required
def mes_cours(request):
    """Cours de l'utilisateur connecté (professeur uniquement)"""
    if not request.user.est_professeur():
        messages.warning(
            request,
            "Cette fonctionnalité n'est disponible que pour les professeurs.",
        )
        return redirect("accueil")

    professeur = request.user.profil_professeur
    sections = (
        professeur.sections_cours
        .select_related("cours")
        .annotate(
            nb_inscrits=Count(
                "inscriptions",
                filter=Q(inscriptions__statut__in=["INSCRIT", "COMPLETE", "EN_COURS"])
            )
        )
        .order_by("-annee", "cours__code")
    )

    contexte = {
        "sections": sections,
        "est_professeur": True,
        "nombre_cours": sections.count(),
    }
    return render(request, "cours/mes_cours.html", contexte)