import csv
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Min, Q, Case, When, IntegerField
from django.conf import settings
from collections import defaultdict
from django.template.loader import render_to_string
from django.utils.timezone import now
from .models import (
    Note,
    HistoriqueNote,
    Bulletin,
)  # ← corrigé (était Grade, GradeHistory, Transcript)
from applications.inscriptions.models import Inscription  # ← corrigé (était Enrollment)
from applications.cours.models import SectionCours  # ← corrigé (était CourseSection)
from .forms import FormulaireNote  # ← corrigé (était GradeForm)
from utilitaires.roles import (
    est_administrateur,
    est_professeur,
    est_etudiant,
)  # ← corrigé (était is_admin, is_professor, is_student)
from applications.comptes.models import (
    Utilisateur,
    Etudiant,
)  # ← corrigé (était User, Student)
from applications.departements.models import Departement  # ← corrigé (était Department)
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from collections import defaultdict
# ===========================================================================
# VUES PROFESSEUR
# ===========================================================================


STATUTS_VISIBLES = ["INSCRIT", "COMPLETE", "ECHOUE"]

@login_required
@user_passes_test(est_professeur)
def vue_sections_professeur(request):
    """Sections du professeur pour la saisie des notes"""
    if request.user.is_superuser:
        sections = SectionCours.objects.all().select_related("cours", "professeur")
    else:
        professeur = request.user.profil_professeur
        sections = professeur.sections_cours.select_related("cours").annotate(
            nb_inscrits=Count(
                "inscriptions",
                filter=Q(inscriptions__statut__in=STATUTS_VISIBLES)  # ← ici
            )
        )

    contexte = {"sections": sections}
    return render(request, "notes/sections_professeur.html", contexte)


@login_required
@user_passes_test(est_professeur)
def vue_saisie_notes(request, id_section):
    """Saisie des notes pour une section"""
    section = get_object_or_404(SectionCours, id=id_section)

    if not request.user.is_superuser:
        if section.professeur != request.user.profil_professeur:
            messages.error(request, "Vous n'avez pas accès à cette section.")
            return redirect("notes:sections_professeur")

    id_inscription = request.GET.get("inscription")

    inscriptions = section.inscriptions.filter(
        statut__in=Inscription.STATUTS_ACTIFS
    ).select_related(
        "etudiant__utilisateur",
        "note",  # ← précharge la note directement
    )

    if id_inscription:
        inscriptions = inscriptions.order_by(
            Case(
                When(id=id_inscription, then=0),
                default=1,
                output_field=IntegerField(),
            ),
            "etudiant__numero_etudiant",
        )
    else:
        inscriptions = inscriptions.order_by("etudiant__numero_etudiant")

    if request.method == "POST":
        note_par = (
            section.professeur
            if request.user.is_superuser
            else request.user.profil_professeur
        )

        for inscription in inscriptions:
            note, creee = Note.objects.get_or_create(
                inscription=inscription, defaults={"note_par": note_par}
            )

            anciennes_valeurs = {
                "examen_mi_parcours": note.examen_mi_parcours,
                "examen_final":       note.examen_final,
                "travaux":            note.travaux,
                "participation":      note.participation,
                "projet":             note.projet,
            }

            for composante in anciennes_valeurs:
                cle_champ = f"note_{inscription.id}_{composante}"
                valeur = request.POST.get(cle_champ)
                if valeur:
                    try:
                        nouvelle_valeur = float(valeur)
                        ancienne_valeur = anciennes_valeurs[composante]

                        if ancienne_valeur != nouvelle_valeur:
                            HistoriqueNote.objects.create(
                                note=note,
                                composante=composante,
                                ancienne_valeur=ancienne_valeur,
                                nouvelle_valeur=nouvelle_valeur,
                                modifie_par=note_par,
                            )
                        setattr(note, composante, nouvelle_valeur)
                    except ValueError:
                        pass

            commentaires = request.POST.get(f"commentaires_{inscription.id}")
            if commentaires:
                note.commentaires = commentaires

            note.note_par = note_par
            note.save()

        messages.success(request, "Notes enregistrées avec succès.")
        return redirect("notes:saisie_notes_professeur", id_section=section.id)


    inscription_notes = []
    for inscription in inscriptions:
        # select_related("note") garantit que la note est déjà en cache ORM
        # pas de requête supplémentaire, pas de risque d'objet None inattendu
        try:
            note = inscription.note
        except Note.DoesNotExist:
            note = None
        inscription_notes.append({"inscription": inscription, "note": note})

    contexte = {
        "section":           section,
        "inscription_notes": inscription_notes,
    }
    return render(request, "notes/saisie_notes.html", contexte)


PONDERATIONS_NOTE = [
    ("examen_mi_parcours", "Examen mi-parcours", 25),
    ("examen_final", "Examen final", 35),
    ("travaux", "Travaux pratiques", 20),
    ("participation", "Participation", 10),
    ("projet", "Projet", 10),
]


@login_required
@user_passes_test(est_etudiant)
def vue_mes_notes(request):
    """Mes notes (vue étudiant)"""
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect("accueil")

    etudiant = request.user.profil_etudiant
    etudiant = (
        Etudiant.objects
        .select_related("utilisateur", "departement")
        .get(utilisateur=request.user)
    )
    inscriptions = (
        etudiant.inscriptions.filter(statut__in=["INSCRIT", "COMPLETE"])
        .select_related(
            "section_cours__cours", "section_cours__professeur__utilisateur"
        )
        .order_by("-date_inscription")
    )

    inscription_notes = []
    total_points = 0
    total_credits = 0

    for inscription in inscriptions:
        try:
            note = inscription.note
            if note.note_finale:
                credits = inscription.section_cours.cours.credits
                total_points += float(note.note_finale) * credits
                total_credits += credits
        except Note.DoesNotExist:
            note = None

        composantes = []
        if note:
            for champ, label, poids in PONDERATIONS_NOTE:
                valeur = getattr(note, champ)
                points = (
                    round(float(valeur) * poids / 100, 2)
                    if valeur is not None
                    else None
                )
                composantes.append(
                    {"label": label, "poids": poids, "valeur": valeur, "points": points}
                )

        inscription_notes.append(
            {"inscription": inscription, "note": note, "composantes": composantes}
        )

    moyenne = round(total_points / total_credits, 2) if total_credits > 0 else None

    contexte = {
        "etudiant":          etudiant,   # ← manquait
        "inscription_notes": inscription_notes,
        "moyenne": moyenne,
        "total_credits": total_credits,
    }
    

    return render(request, "notes/mes_notes.html", contexte)


@login_required
def vue_detail_note(request, id_note):
    """Détail d'une note"""
    note = get_object_or_404(
        Note.objects.select_related(
            "inscription__etudiant__utilisateur",
            "inscription__section_cours__cours",
            "note_par__utilisateur",
        ),
        id=id_note,
    )

    peut_voir = request.user.is_superuser or request.user.est_administrateur()

    if not peut_voir and request.user.est_etudiant():
        peut_voir = note.inscription.etudiant == request.user.profil_etudiant

    if not peut_voir and request.user.est_professeur():
        peut_voir = (
            note.inscription.section_cours.professeur == request.user.profil_professeur
        )

    if not peut_voir:
        messages.error(request, "Vous n'avez pas la permission de voir cette note.")
        return redirect("accueil")

    historique = note.historique.select_related("modifie_par__utilisateur").order_by(
        "-modifie_le"
    )

    contexte = {"note": note, "historique": historique}
    return render(request, "notes/detail_note.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def vue_liste_notes(request):
    """Liste de toutes les notes groupées par étudiant (admin)"""
    notes_qs = Note.objects.select_related(
        "inscription__etudiant__utilisateur",
        "inscription__section_cours__cours",
        "inscription__section_cours__professeur__utilisateur",
        "note_par__utilisateur",
    )

    numero_etudiant = request.GET.get("numero_etudiant", "").strip()
    code_cours = request.GET.get("code_cours", "").strip()
    note_min = request.GET.get("note_min", "").strip()
    note_max = request.GET.get("note_max", "").strip()

    if numero_etudiant:
        notes_qs = notes_qs.filter(
            inscription__etudiant__numero_etudiant__icontains=numero_etudiant
        )
    if code_cours:
        notes_qs = notes_qs.filter(
            inscription__section_cours__cours__code__icontains=code_cours
        )
    if note_min:
        try:
            notes_qs = notes_qs.filter(note_finale__gte=float(note_min))
        except ValueError:
            pass
    if note_max:
        try:
            notes_qs = notes_qs.filter(note_finale__lte=float(note_max))
        except ValueError:
            pass

    notes_qs = notes_qs.order_by("-cree_le")
    toutes_notes = list(notes_qs)

    # Grouper par étudiant
    groupes = []
    etudiant_courant = None
    groupe_courant = []

    for note in toutes_notes:
        num = note.inscription.etudiant.numero_etudiant
        if etudiant_courant != num:
            if groupe_courant:
                groupes.append(
                    {
                        "etudiant": groupe_courant[0].inscription.etudiant,
                        "notes": groupe_courant,
                        "total": len(groupe_courant),
                    }
                )
            etudiant_courant = num
            groupe_courant = [note]
        else:
            groupe_courant.append(note)

    if groupe_courant:
        groupes.append(
            {
                "etudiant": groupe_courant[0].inscription.etudiant,
                "notes": groupe_courant,
                "total": len(groupe_courant),
            }
        )

    elements_par_page = getattr(settings, "ELEMENTS_PAR_PAGE", 20)
    paginateur = Paginator(groupes, elements_par_page)
    numero_page = request.GET.get("page", 1)
    page_obj = paginateur.get_page(numero_page)

    contexte = {
        "groupes": page_obj.object_list,
        "page_obj": page_obj,
        "total_etudiants": len(groupes),
        "total_notes": len(toutes_notes),
    }
    return render(request, "notes/liste_notes.html", contexte)


@login_required
@user_passes_test(est_etudiant)
def vue_mes_professeurs(request):
    """Affiche les professeurs des cours de l'étudiant connecté"""
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect("accueil")

    etudiant = request.user.profil_etudiant

    inscriptions = etudiant.inscriptions.filter(
        statut__in=["INSCRIT", "COMPLETE"]
    ).select_related("section_cours__cours", "section_cours__professeur__utilisateur")

    professeurs = set()
    for inscription in inscriptions:
        prof_utilisateur = getattr(
            inscription.section_cours.professeur, "utilisateur", None
        )
        if prof_utilisateur:
            professeurs.add(prof_utilisateur)

    contexte = {
        "professeurs": professeurs,
        "inscriptions": inscriptions,
    }
    return render(request, "notes/mes_professeurs.html", contexte)




@login_required
@user_passes_test(est_etudiant)
def vue_releve_notes(request):
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect("accueil")

    etudiant = request.user.profil_etudiant

    inscriptions = (
        etudiant.inscriptions.filter(statut__in=["INSCRIT", "COMPLETE"])
        .select_related("section_cours__cours", "note")
        .order_by("-section_cours__annee", "section_cours__semestre")
    )

    periodes       = defaultdict(list)
    total_notes    = 0
    total_cours    = 0
    credits_cumules = 0

    for inscription in inscriptions:
        cle_periode = (
            inscription.section_cours.annee,
            inscription.section_cours.semestre,
        )
        try:
            note = inscription.note
            if note.note_finale:
                periodes[cle_periode].append({
                    "inscription": inscription,
                    "note": note
                })
                total_notes     += float(note.note_finale)
                total_cours     += 1
                credits_cumules += inscription.section_cours.cours.credits
        except Note.DoesNotExist:
            pass

    moyenne_generale = round(total_notes / total_cours, 2) if total_cours > 0 else 0

    if moyenne_generale >= 90:
        mention_generale = "Excellent"
    elif moyenne_generale >= 80:
        mention_generale = "Très bien"
    elif moyenne_generale >= 70:
        mention_generale = "Bien"
    elif moyenne_generale >= 60:
        mention_generale = "Passable"
    else:
        mention_generale = "Échec"

    periodes_triees = sorted(
        periodes.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True
    )

    contexte = {
        "etudiant":          etudiant,
        "periodes":          periodes_triees,
        "total_cours":       total_cours,
        "credits_cumules":   credits_cumules,
        "moyenne_generale":  moyenne_generale,
        "mention_generale":  mention_generale,
    }
    return render(request, "notes/releve_notes.html", contexte)


@login_required
@user_passes_test(est_etudiant)
def vue_telecharger_releve(request):
    """Génère et télécharge le relevé de notes en PDF via WeasyPrint"""
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect("accueil")

    etudiant = (
        Etudiant.objects
        .select_related("utilisateur", "departement")
        .get(utilisateur=request.user)
    )

    from applications.portail.models import SiteSettings
    site = SiteSettings.get()

    inscriptions = (
        etudiant.inscriptions.filter(statut__in=["INSCRIT", "COMPLETE"])
        .select_related("section_cours__cours", "note")
        .order_by("-section_cours__annee", "section_cours__semestre")
    )

    periodes        = defaultdict(list)
    credits_cumules = 0
    total_notes     = 0
    total_cours     = 0

    for inscription in inscriptions:
        cle_periode = (
            inscription.section_cours.annee,
            inscription.section_cours.semestre,
        )
        try:
            note = inscription.note
            if note.note_finale:
                periodes[cle_periode].append({"inscription": inscription, "note": note})
                credits_cumules += inscription.section_cours.cours.credits
                total_notes     += float(note.note_finale)
                total_cours     += 1
        except Note.DoesNotExist:
            pass

    moyenne_generale = round(total_notes / total_cours, 2) if total_cours > 0 else 0

    if moyenne_generale >= 90:   mention_generale = "Excellent"
    elif moyenne_generale >= 80: mention_generale = "Très bien"
    elif moyenne_generale >= 70: mention_generale = "Bien"
    elif moyenne_generale >= 60: mention_generale = "Passable"
    else:                        mention_generale = "Échec"

    periodes_triees = sorted(
        periodes.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True
    )

    contexte = {
        "etudiant":          etudiant,
        "site":              site,
        "periodes":          periodes_triees,
        "moyenne_generale":  moyenne_generale,
        "mention_generale":  mention_generale,
        "credits_cumules":   credits_cumules,
        "total_cours":       total_cours,
        "now":               now(),
    }

    # Rendu HTML → PDF
    html_string = render_to_string("notes/releve_pdf.html", contexte, request=request)

    from weasyprint import HTML, CSS
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    nom_fichier = f"releve_{etudiant.numero_etudiant}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    return response


@login_required
@user_passes_test(est_administrateur)
def vue_generer_releve(request, id_etudiant):
    """Générer un relevé de notes pour un étudiant (admin)"""
    etudiant = get_object_or_404(Etudiant, id=id_etudiant)


        # ✅ Après — inclure INSCRIT et COMPLETE, exclure ABANDONNE
    inscriptions = (
        etudiant.inscriptions.filter(statut__in=["INSCRIT", "COMPLETE"])
        .select_related("section_cours__cours", "note")
        .order_by("-section_cours__annee", "section_cours__semestre")
    )

    periodes = defaultdict(list)
    credits_cumules = 0
    points_cumules = 0

    for inscription in inscriptions:
        cle_periode = (
            inscription.section_cours.annee,
            inscription.section_cours.semestre,
        )
        try:
            note = inscription.note
            if note.note_finale:
                periodes[cle_periode].append({"inscription": inscription, "note": note})
                credits = inscription.section_cours.cours.credits
                val_note = float(note.note_finale)
                if val_note >= 90:
                    points = 4.0
                elif val_note >= 80:
                    points = 3.0
                elif val_note >= 70:
                    points = 2.0
                elif val_note >= 60:
                    points = 1.0
                else:
                    points = 0.0
                points_cumules += points * credits
                credits_cumules += credits
        except Note.DoesNotExist:
            pass

    gpa_final = round(points_cumules / credits_cumules, 2) if credits_cumules > 0 else 0
    periodes_triees = sorted(
        periodes.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True
    )

    contexte = {
        "etudiant": etudiant,
        "periodes": periodes_triees,
        "credits_cumules": credits_cumules,
        "gpa_final": gpa_final,
    }
    return render(request, "notes/releve_notes.html", contexte)


@login_required
def vue_statistiques_cours(request, id_section):
    """Statistiques d'un cours"""
    section = get_object_or_404(SectionCours, id=id_section)

    peut_voir = request.user.is_superuser or request.user.est_administrateur()
    if not peut_voir and request.user.est_professeur():
        peut_voir = section.professeur == request.user.profil_professeur

    if not peut_voir:
        messages.error(
            request, "Vous n'avez pas la permission de voir ces statistiques."
        )
        return redirect("accueil")

    # ✅ INSCRIT + COMPLETE (les notes complètes ont statut COMPLETE)
    notes = Note.objects.filter(
        inscription__section_cours=section,
        inscription__statut__in=["INSCRIT", "COMPLETE"],
        note_finale__isnull=False,
    )

    stats = notes.aggregate(
        moyenne=Avg("note_finale"),
        total=Count("id"),
        maximum=Max("note_finale"),
        minimum=Min("note_finale"),
    )

    # ✅ Clés alignées avec le template (Excellent, Tres_bien, Bien, Passable, Echec)
    MENTION_KEYS = {
        "Excellent": "Excellent",
        "Très bien": "Tres_bien",
        "Bien":      "Bien",
        "Passable":  "Passable",
        "Échec":     "Echec",
    }

    distribution = {
        key: notes.filter(mention=label).count()
        for label, key in MENTION_KEYS.items()
    }

    total = stats["total"] or 0

    pourcentages = {
        key: round(nb * 100 / total, 1) if total > 0 else 0
        for key, nb in distribution.items()
    }

    nb_reussite = (
        distribution["Excellent"]
        + distribution["Tres_bien"]
        + distribution["Bien"]
        + distribution["Passable"]
    )
    taux_reussite = round(nb_reussite * 100 / total, 0) if total > 0 else None

    contexte = {
        "section":        section,
        "stats":          stats,
        "distribution":   distribution,
        "pourcentages":   pourcentages,
        "taux_reussite":  taux_reussite,
    }
    return render(request, "notes/statistiques_cours.html", contexte)


@login_required
@user_passes_test(est_professeur)
def vue_recap_notes(request, id_section):
    section = get_object_or_404(SectionCours, id=id_section)

    if not request.user.is_superuser:
        if section.professeur != request.user.profil_professeur:
            messages.error(request, "Vous n'avez pas accès à cette section.")
            return redirect("notes:sections_professeur")

    inscriptions = (
        section.inscriptions.filter(statut__in=Inscription.STATUTS_ACTIFS)
        .select_related("etudiant__utilisateur")
        .order_by("etudiant__numero_etudiant")
    )

    inscription_notes = []
    nb_notes_saisies = 0
    total_notes = []

    for inscription in inscriptions:
        try:
            note = inscription.note
            if note.note_finale:
                nb_notes_saisies += 1
                total_notes.append(float(note.note_finale))
        except Note.DoesNotExist:
            note = None
        inscription_notes.append({"inscription": inscription, "note": note})

    nb_en_attente = len(inscription_notes) - nb_notes_saisies
    moyenne_section = sum(total_notes) / len(total_notes) if total_notes else None

    contexte = {
        "section":           section,
        "inscription_notes": inscription_notes,  # ← nom correct
        "nb_notes_saisies":  nb_notes_saisies,
        "nb_en_attente":     nb_en_attente,
        "moyenne_section":   moyenne_section,
    }
    return render(request, "notes/resume_notes.html", contexte)


@login_required
@user_passes_test(est_professeur)
def vue_mes_etudiants(request):
    """Liste de tous les étudiants du professeur"""
    if request.user.is_superuser:
        sections = SectionCours.objects.all()
    else:
        professeur = request.user.profil_professeur
        sections = professeur.sections_cours.all()

    STATUTS_VISIBLES = ["INSCRIT", "COMPLETE", "ECHOUE"]

    inscriptions = (
        Inscription.objects.filter(
            section_cours__in=sections,
            statut__in=STATUTS_VISIBLES,
        )
        .select_related("etudiant__utilisateur", "section_cours__cours")
        .distinct()
    )

    donnees_etudiants = defaultdict(
        lambda: {
            "etudiant":      None,
            "cours":         [],
            "total_credits": 0,
            "nb_notes":      0,
            "total_points":  0,
            "moyenne":       None,  # ✅ sur 100, remplace gpa
        }
    )

    for inscription in inscriptions:
        etudiant = inscription.etudiant
        cle = etudiant.id

        if donnees_etudiants[cle]["etudiant"] is None:
            donnees_etudiants[cle]["etudiant"] = etudiant

        donnees_etudiants[cle]["cours"].append({
            "cours":       inscription.section_cours.cours,
            "section":     inscription.section_cours,
            "inscription": inscription,
        })

        try:
            note = inscription.note
            if note.note_finale:
                credits = inscription.section_cours.cours.credits
                donnees_etudiants[cle]["total_credits"] += credits
                donnees_etudiants[cle]["nb_notes"]      += 1
                # ✅ moyenne pondérée sur 100 directement
                donnees_etudiants[cle]["total_points"]  += float(note.note_finale) * credits
        except Exception:
            pass

    for cle in donnees_etudiants:
        d = donnees_etudiants[cle]
        if d["total_credits"] > 0:
            d["moyenne"] = round(d["total_points"] / d["total_credits"], 2)

    liste_etudiants = list(donnees_etudiants.values())

    recherche = request.GET.get("recherche", "")
    if recherche:
        liste_etudiants = [
            s for s in liste_etudiants
            if recherche.lower() in s["etudiant"].utilisateur.get_full_name().lower()
            or recherche.lower() in s["etudiant"].numero_etudiant.lower()
        ]

    paginateur = Paginator(liste_etudiants, getattr(settings, "ELEMENTS_PAR_PAGE", 20))
    page_obj = paginateur.get_page(request.GET.get("page"))

    contexte = {
        "page_obj":        page_obj,
        "recherche":       recherche,
        "total_etudiants": len(liste_etudiants),
    }
    return render(request, "notes/mes_etudiants.html", contexte)

@login_required
@user_passes_test(est_professeur)
def vue_palmares(request):
    """
    Palmarès par section — sélection obligatoire.
    """
    if request.user.is_superuser:
        toutes_sections = (
            SectionCours.objects.all()
            .select_related("cours", "cours__departement")
            .order_by("-annee", "semestre", "cours__code")
        )
    else:
        professeur = request.user.profil_professeur
        toutes_sections = (
            professeur.sections_cours.all()
            .select_related("cours", "cours__departement")
            .order_by("-annee", "semestre", "cours__code")
        )

    id_section     = request.GET.get("section", "").strip()
    recherche      = request.GET.get("recherche", "").strip()

    section_active = None
    palmares       = []
    moy_note       = 0
    top_etudiant   = None
    nb_avec_note   = 0
    nb_sans_note   = 0

    if id_section:
        try:
            section_active = toutes_sections.get(id=id_section)
        except SectionCours.DoesNotExist:
            section_active = None

    if section_active:
        inscriptions = (
            Inscription.objects.filter(
                section_cours=section_active,
                statut__in=Inscription.STATUTS_ACTIFS,
            )
            .select_related(
                "etudiant__utilisateur",
                "etudiant__departement",
            )
            .prefetch_related("note")
        )

        donnees_brutes = []

        for inscription in inscriptions:
            etudiant = inscription.etudiant
            note_val = None
            mention  = ""

            try:
                note_obj = inscription.note
                if note_obj.note_finale is not None:
                    note_val = float(note_obj.note_finale)
                    mention  = note_obj.mention or ""
                    nb_avec_note += 1
                else:
                    nb_sans_note += 1
            except Exception:
                nb_sans_note += 1

            donnees_brutes.append({
                "etudiant": etudiant,
                "note":     note_val,
                "mention":  mention,
            })

        if recherche:
            donnees_brutes = [
                d for d in donnees_brutes
                if recherche.lower() in d["etudiant"].utilisateur.get_full_name().lower()
                or recherche.lower() in d["etudiant"].numero_etudiant.lower()
            ]

        avec_note = [d for d in donnees_brutes if d["note"] is not None]
        sans_note = [d for d in donnees_brutes if d["note"] is None]

        avec_note.sort(key=lambda x: x["note"], reverse=True)

        # ✅ Mentions palmarès alignées sur le système français du modèle
        for rang, d in enumerate(avec_note, start=1):
            d["rang"] = rang
            n = d["note"]
            if n >= 90:
                d["mention_palmares"] = "Excellent"
                d["classe_mention"]   = "summa"
            elif n >= 80:
                d["mention_palmares"] = "Très bien"
                d["classe_mention"]   = "magna"
            elif n >= 70:
                d["mention_palmares"] = "Bien"
                d["classe_mention"]   = "cum"
            elif n >= 60:
                d["mention_palmares"] = "Passable"
                d["classe_mention"]   = "passable"
            else:
                d["mention_palmares"] = "Échec"
                d["classe_mention"]   = "insuffisant"

        for d in sans_note:
            d["rang"]             = "—"
            d["mention_palmares"] = "Note manquante"
            d["classe_mention"]   = "passable"

        palmares = avec_note + sans_note

        if avec_note:
            moy_note     = round(sum(d["note"] for d in avec_note) / len(avec_note), 2)
            top_etudiant = avec_note[0]

    contexte = {
        "sections":        toutes_sections,
        "section_active":  section_active,
        "id_section":      id_section,
        "palmares":        palmares,
        "recherche":       recherche,
        "total_etudiants": len(palmares),
        "nb_avec_note":    nb_avec_note,
        "nb_sans_note":    nb_sans_note,
        "moy_note":        moy_note,
        "top_etudiant":    top_etudiant,
        "choix_semestre":  SectionCours.CHOIX_SEMESTRE,
    }
    return render(request, "notes/palmares.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def vue_gpa_etudiants(request):
    """GPA de tous les étudiants avec filtres (admin)"""
    departement = request.GET.get("departement")
    annee = request.GET.get("annee")

    etudiants = Utilisateur.objects.filter(role="ETUDIANT", is_active=True)

    if departement:
        etudiants = etudiants.filter(profil_etudiant__departement__code=departement)
    if annee:
        etudiants = etudiants.filter(profil_etudiant__niveau=annee)

    liste_gpa = []
    for utilisateur in etudiants.select_related("profil_etudiant__departement"):
        etudiant = utilisateur.profil_etudiant
        inscriptions = etudiant.inscriptions.filter(
            statut__in=["INSCRIT", "COMPLETE"]
        ).select_related("section_cours__cours")

        total_points = 0
        total_credits = 0

        for inscription in inscriptions:
            try:
                note = inscription.note
                if note.note_finale is not None:
                    credits = inscription.section_cours.cours.credits
                    total_points += float(note.note_finale) * credits
                    total_credits += credits
            except Note.DoesNotExist:
                continue

        gpa = round(total_points / total_credits, 2) if total_credits > 0 else None
        liste_gpa.append(
            {
                "etudiant": utilisateur,
                "departement": (
                    etudiant.departement.nom if etudiant.departement else "-"
                ),
                "annee": etudiant.get_niveau_display(),
                "gpa": gpa,
                "total_credits": total_credits,
                "nb_cours": inscriptions.count(),
            }
        )

    paginateur = Paginator(liste_gpa, getattr(settings, "ELEMENTS_PAR_PAGE", 20))
    page_obj = paginateur.get_page(request.GET.get("page"))
    departements = Departement.objects.values_list("code", "nom")
    annees = Etudiant.CHOIX_ANNEE

    contexte = {
        "page_obj": page_obj,
        "departements": departements,
        "annees": annees,
        "departement_choisi": departement,
        "annee_choisie": annee,
    }
    return render(request, "notes/moyenne_generale_etudiants.html", contexte)


# ===========================================================================
# CRUD ADMIN
# ===========================================================================


@login_required
@user_passes_test(est_administrateur)
def modifier_note(request, id_note):
    """Modifier une note existante (admin)"""
    note = get_object_or_404(Note, id=id_note)

    if request.method == "POST":
        form = FormulaireNote(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            if request.user.is_superuser:
                note.note_par = note.inscription.section_cours.professeur or None
            else:
                note.note_par = request.user.profil_professeur
            note.save()
            messages.success(request, "Note mise à jour avec succès.")
            return redirect("notes:liste_notes_admin")
    else:
        form = FormulaireNote(instance=note)

    contexte = {"form": form, "note": note, "action": "Modifier"}
    return render(request, "notes/formulaire_note.html", contexte)


@login_required
@user_passes_test(est_professeur)
def modifier_note_professeur(request, id_note):
    """Modifier une note (professeur)"""
    note = get_object_or_404(Note, id=id_note)

    if note.inscription.section_cours.professeur.utilisateur != request.user:
        return HttpResponseForbidden(
            "Vous n'avez pas la permission de modifier cette note."
        )

    if request.method == "POST":
        form = FormulaireNote(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            note.note_par = request.user.profil_professeur
            note.save()
            messages.success(request, "Note mise à jour avec succès.")
            return redirect(
                "notes:saisie_notes_professeur",
                id_section=note.inscription.section_cours.id,
            )
    else:
        form = FormulaireNote(instance=note)

    return render(
        request,
        "notes/formulaire_note.html",
        {"form": form, "note": note, "action": "Modifier"},
    )


@login_required
@user_passes_test(est_professeur)
def saisie_modifier_note_professeur(request, id_inscription):
    """
    Vue unique pour un étudiant donné :
    - s'il n'a pas encore de note pour cette inscription -> formulaire de SAISIE (vide)
    - s'il en a déjà une -> formulaire de MODIFICATION (champs pré-remplis)
    """
    inscription = get_object_or_404(
        Inscription.objects.select_related(
            "etudiant__utilisateur", "section_cours__cours", "section_cours__professeur"
        ),
        id=id_inscription,
    )

    if not request.user.is_superuser:
        if inscription.section_cours.professeur != request.user.profil_professeur:
            messages.error(request, "Vous n'avez pas accès à cette inscription.")
            return redirect("notes:sections_professeur")

    # Note existante (instance liée) OU nouvelle instance non sauvegardée,
    # déjà rattachée à l'inscription : c'est ce qui fait basculer
    # automatiquement le formulaire en mode "Saisir" ou "Modifier".
    note = Note.objects.filter(inscription=inscription).first()
    creation = note is None
    if creation:
        note = Note(inscription=inscription)

    if request.method == "POST":
        form = FormulaireNote(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            note.inscription = inscription  # sécurité : on impose la bonne inscription
            note.note_par = (
                inscription.section_cours.professeur
                if request.user.is_superuser
                else request.user.profil_professeur
            )
            note.save()
            messages.success(
                request,
                "Note enregistrée avec succès." if creation else "Note mise à jour avec succès.",
            )
            return redirect(
                "notes:saisie_notes_professeur",
                id_section=inscription.section_cours.id,
            )
    else:
        form = FormulaireNote(instance=note)

    contexte = {
        "form": form,
        "note": note if not creation else None,
        "inscription": inscription,
        "action": "Saisir" if creation else "Modifier",
    }
    return render(request, "notes/formulaire_note.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def supprimer_note(request, id_note):
    """Supprimer une note (admin)"""
    note = get_object_or_404(Note, id=id_note)

    if request.method == "POST":
        nom_etudiant = note.inscription.etudiant.utilisateur.get_full_name()
        code_cours = note.inscription.section_cours.cours.code
        note.delete()
        messages.success(request, f"Note supprimée pour {nom_etudiant} - {code_cours}")
        return redirect("notes:liste_notes_admin")

    return render(request, "notes/confirmer_suppression_note.html", {"note": note})


@login_required
@user_passes_test(est_administrateur)
def saisie_notes_groupee(request):
    """Saisie en masse des notes pour une section (admin)"""
    id_section = request.GET.get("section_id")
    section = None
    inscriptions = []

    if id_section:
        section = get_object_or_404(SectionCours, id=id_section)
        inscriptions = (
            Inscription.objects.filter(
                section_cours=section,
                statut__in=Inscription.STATUTS_ACTIFS,  # ✅ INSCRIT + COMPLETE
            )
            .select_related("etudiant__utilisateur")
            .order_by("etudiant__numero_etudiant")
        )

    if request.method == "POST":
        nb_mises_a_jour = 0
        note_par = section.professeur if section and section.professeur else None

        COMPOSANTES = {
            "examen_mi_parcours",
            "examen_final",
            "travaux",
            "participation",
            "projet",
        }

        for inscription in inscriptions:
            note, _ = Note.objects.get_or_create(
                inscription=inscription,
                defaults={"note_par": note_par},
            )
            modifie = False
            for composante in COMPOSANTES:
                cle = f"note_{inscription.id}_{composante}"
                valeur = request.POST.get(cle)
                if valeur:
                    try:
                        setattr(note, composante, float(valeur))
                        modifie = True
                    except ValueError:
                        pass

            commentaire = request.POST.get(f"commentaires_{inscription.id}")
            if commentaire is not None:
                note.commentaires = commentaire
                modifie = True

            if modifie:
                note.note_par = note_par
                note.save()
                nb_mises_a_jour += 1

        messages.success(request, f"{nb_mises_a_jour} note(s) mise(s) à jour.")
        return redirect(f"/notes/saisie-groupee/?section_id={id_section}")

    # ✅ GET : on ne crée plus de notes vides, on charge celles qui existent
    notes_dict = {}
    if section:
        notes = Note.objects.filter(
            inscription__section_cours=section
        ).select_related("inscription__etudiant__utilisateur")
        notes_dict = {n.inscription_id: n for n in notes}

    for inscription in inscriptions:
        inscription.note_obj = notes_dict.get(inscription.id)

    toutes_sections = SectionCours.objects.all().order_by(
        "cours__code", "numero_section"
    )

    contexte = {
        "section":        section,
        "inscriptions":   inscriptions,
        "notes_dict":     notes_dict,
        "toutes_sections": toutes_sections,
    }
    return render(request, "notes/saisie_notes_groupee.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def recalculer_notes(request):
    """Recalculer toutes les notes finales"""
    if request.method == "POST":
        notes = Note.objects.all()
        total = 0
        for note in notes:
            note.save()  # déclenche calculer_note_finale() automatiquement
            total += 1
        messages.success(request, f"{total} note(s) recalculée(s).")
        return redirect("notes:statistiques_notes")

    total_notes = Note.objects.count()
    return render(request, "notes/recalculer_notes.html", {"total_notes": total_notes})


@login_required
@user_passes_test(est_administrateur)
def exporter_notes(request):
    """Exporter les notes en CSV"""
    notes = Note.objects.select_related(
        "inscription__etudiant__utilisateur",
        "inscription__section_cours__cours",
        "note_par__utilisateur",
    ).order_by(
        "inscription__etudiant__numero_etudiant",
        "inscription__section_cours__cours__code",
    )

    numero_etudiant = request.GET.get("numero_etudiant")
    code_cours = request.GET.get("code_cours")

    if numero_etudiant:
        notes = notes.filter(
            inscription__etudiant__numero_etudiant__icontains=numero_etudiant
        )
    if code_cours:
        notes = notes.filter(
            inscription__section_cours__cours__code__icontains=code_cours
        )

    reponse = HttpResponse(content_type="text/csv; charset=utf-8")
    reponse["Content-Disposition"] = 'attachment; filename="notes_export.csv"'
    reponse.write("\ufeff")  # BOM pour Excel

    writer = csv.writer(reponse)
    writer.writerow(
        [
            "Matricule",
            "Nom complet",
            "Code cours",
            "Section",
            "Mi-parcours",
            "Examen final",
            "Travaux",
            "Participation",
            "Projet",
            "Note finale",
            "Mention",
            "Noté par",
            "Date modification",
        ]
    )

    for note in notes:
        writer.writerow(
            [
                note.inscription.etudiant.numero_etudiant,
                note.inscription.etudiant.utilisateur.get_full_name(),
                note.inscription.section_cours.cours.code,
                note.inscription.section_cours.numero_section,
                note.examen_mi_parcours or "",
                note.examen_final or "",
                note.travaux or "",
                note.participation or "",
                note.projet or "",
                note.note_finale or "",
                note.mention or "",
                note.note_par.utilisateur.get_full_name() if note.note_par else "",
                note.modifie_le.strftime("%d/%m/%Y %H:%M"),
            ]
        )

    return reponse


@login_required
@user_passes_test(est_administrateur)
def vue_statistiques_notes(request):
    """Statistiques détaillées des notes (admin)"""
    stats = Note.objects.aggregate(
        total=Count("id"),
        moyenne=Avg("note_finale"),
        maximum=Max("note_finale"),
        minimum=Min("note_finale"),
    )

    MENTION_KEYS = {
        "Excellent": "Excellent",
        "Très bien": "Tres_bien",
        "Bien":      "Bien",
        "Passable":  "Passable",
        "Échec":     "Echec",
    }

    distribution = {
        key: Note.objects.filter(mention=label).count()
        for label, key in MENTION_KEYS.items()
    }

    total = stats["total"] or 0
    pourcentages = {
        key: (nb / total * 100) if total > 0 else 0
        for key, nb in distribution.items()
    }

    stats_departements = []
    for dept in Departement.objects.all():
        agg = Note.objects.filter(
            inscription__section_cours__cours__departement=dept
        ).aggregate(total=Count("id"), moyenne=Avg("note_finale"))
        if agg["total"]:
            stats_departements.append(
                {"nom": dept.nom, "total": agg["total"], "moyenne": agg["moyenne"]}
            )

    top_etudiants = (
        Etudiant.objects
        .annotate(moyenne=Avg("inscriptions__note__note_finale"))
        .filter(moyenne__isnull=False)
        .select_related("utilisateur", "departement")
        .order_by("-moyenne")[:10]
    )

    contexte = {
        "stats": stats,
        "distribution": distribution,
        "pourcentages": pourcentages,
        "stats_departements": stats_departements,
        "top_etudiants": top_etudiants,
    }
    return render(request, "notes/statistiques.html", contexte)


# ===========================================================================
# API AJAX
# ===========================================================================


@login_required
@user_passes_test(est_administrateur)
def recherche_note_ajax(request):
    """Recherche AJAX d'étudiants pour l'auto-complétion"""
    requete = request.GET.get("q", "").strip()

    if len(requete) < 2:
        return JsonResponse({"resultats": []})

    etudiants = Etudiant.objects.filter(
        Q(numero_etudiant__icontains=requete)
        | Q(utilisateur__first_name__icontains=requete)
        | Q(utilisateur__last_name__icontains=requete)
    ).select_related("utilisateur")[:10]

    resultats = [
        {"id": e.id, "text": f"{e.numero_etudiant} - {e.utilisateur.get_full_name()}"}
        for e in etudiants
    ]

    return JsonResponse({"resultats": resultats})