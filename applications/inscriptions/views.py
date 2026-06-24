from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from collections import defaultdict

from .models import Inscription, HistoriqueInscription
from applications.cours.models import SectionCours
from applications.comptes.models import Etudiant
from applications.departements.models import Departement
from utilitaires.roles import est_administrateur, est_etudiant
# ===========================================================================
# VUES ÉTUDIANT
# ===========================================================================


@login_required
@user_passes_test(est_etudiant)
def vue_sections_disponibles(request):
    etudiant = request.user.profil_etudiant

    if etudiant.departement:
        sections = SectionCours.objects.filter(
            cours__niveau=etudiant.niveau,
            cours__departement=etudiant.departement,
        )
    else:
        sections = SectionCours.objects.filter(
            cours__niveau=etudiant.niveau,
            cours__departement__isnull=True,
        )

    sections = sections.select_related("cours", "professeur__utilisateur")

    ids_cours_inscrits = etudiant.inscriptions.filter(statut="INSCRIT").values_list(
        "section_cours__cours_id", flat=True
    )
    sections = sections.exclude(cours_id__in=ids_cours_inscrits)

    session  = request.GET.get("session")
    semestre = request.GET.get("semestre")

    if session:
        sections = sections.filter(session=session)
    if semestre:
        sections = sections.filter(semestre=semestre)

    paginateur = Paginator(sections.order_by("cours__code"), settings.ELEMENTS_PAR_PAGE)
    page_obj   = paginateur.get_page(request.GET.get("page"))

    contexte = {
        "page_obj":             page_obj,
        "choix_session":        SectionCours.CHOIX_SESSION,
        "choix_semestre":       SectionCours.CHOIX_SEMESTRE,
        "max_cours_par_session": settings.MAX_COURS_PAR_SESSION,
    }
    return render(request, "inscriptions/sections_disponibles.html", contexte)

@login_required
@user_passes_test(est_etudiant)
def vue_inscrire(request, id_section):
    """Inscrire l'étudiant connecté à une section"""
    etudiant = request.user.profil_etudiant
    section = get_object_or_404(SectionCours, id=id_section)

    # Déjà inscrit à ce cours (toutes sections confondues) ?
    if Inscription.objects.filter(
        etudiant=etudiant, section_cours__cours=section.cours, statut="INSCRIT"
    ).exists():
        messages.warning(
            request, f"Vous êtes déjà inscrit au cours {section.cours.code}."
        )
        return redirect("inscriptions:mes_inscriptions")

    # Limite de 8 cours par session
    nb_session = Inscription.objects.filter(
        etudiant=etudiant,
        section_cours__session=section.session,
        section_cours__semestre=section.semestre,
        section_cours__annee=section.annee,
        statut="INSCRIT",
    ).count()

    max_cours = getattr(settings, "MAX_COURS_PAR_SESSION", 7)
    if nb_session >= max_cours:
        messages.error(
            request,
            f"Vous avez atteint le maximum de {max_cours} cours pour cette session "
            f"(actuellement inscrit à {nb_session} cours).",
        )
        return redirect("inscriptions:sections_disponibles")

    # Section complète ou fermée ?
    nb_inscrits = Inscription.objects.filter(
        section_cours=section, statut="INSCRIT"
    ).count()
    if section.capacite_max and nb_inscrits >= section.capacite_max:
        messages.error(
            request,
            f"La section {section.numero_section} de {section.cours.code} est complète.",
        )
        return redirect("inscriptions:sections_disponibles")

    if not section.est_ouverte:
        messages.error(
            request,
            f"La section {section.numero_section} de {section.cours.code} est fermée.",
        )
        return redirect("inscriptions:sections_disponibles")

    # Conflits d'horaire
    inscriptions_meme_jour = Inscription.objects.filter(
        etudiant=etudiant,
        section_cours__session=section.session,
        section_cours__semestre=section.semestre,
        section_cours__annee=section.annee,
        section_cours__jour_semaine=section.jour_semaine,
        statut="INSCRIT",
    )
    for insc in inscriptions_meme_jour:
        sect_existante = insc.section_cours
        if sect_existante.conflit_horaire(
            section.jour_semaine, section.heure_debut, section.heure_fin
        ):
            messages.error(
                request,
                f"Conflit d'horaire avec le cours {sect_existante.cours.code}-"
                f"{sect_existante.numero_section} "
                f"({sect_existante.get_jour_semaine_display()} "
                f"{sect_existante.heure_debut.strftime('%H:%M')}-"
                f"{sect_existante.heure_fin.strftime('%H:%M')}).",
            )
            return redirect("inscriptions:sections_disponibles")

    # Créer l'inscription
    try:
        nouvelle_inscription = Inscription(etudiant=etudiant, section_cours=section)
        nouvelle_inscription.full_clean()
        nouvelle_inscription.save()
        messages.success(
            request,
            f"✓ Inscription réussie à {section.cours.code}-{section.numero_section}.",
        )
    except ValidationError as e:
        if hasattr(e, "message_dict"):
            for champ, erreurs in e.message_dict.items():
                for erreur in erreurs:
                    messages.error(request, f"{champ} : {erreur}")
        else:
            for msg in e.messages:
                messages.error(request, msg)
        return redirect("inscriptions:sections_disponibles")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
        return redirect("inscriptions:sections_disponibles")

    return redirect("inscriptions:mes_inscriptions")


@login_required
@user_passes_test(est_etudiant)
def vue_abandonner(request, id_inscription):
    """Abandonner une inscription"""
    inscription = get_object_or_404(
        Inscription, id=id_inscription, etudiant=request.user.profil_etudiant
    )

    if inscription.statut != "INSCRIT":
        messages.warning(request, "Cette inscription ne peut pas être abandonnée.")
        return redirect("inscriptions:mes_inscriptions")

    HistoriqueInscription.objects.create(
        inscription=inscription,
        statut_precedent=inscription.statut,
        nouveau_statut="ABANDONNE",
        modifie_par=request.user,
        raison="Abandonné par l'étudiant",
    )

    inscription.statut = "ABANDONNE"
    inscription.date_abandon = timezone.now()
    inscription.save()

    messages.success(request, "Inscription abandonnée avec succès.")
    return redirect("inscriptions:mes_inscriptions")


@login_required
@user_passes_test(est_etudiant)
def vue_reprendre(request, id_inscription):
    """Reprendre une inscription abandonnée"""
    inscription = get_object_or_404(
        Inscription, id=id_inscription, etudiant=request.user.profil_etudiant
    )

    if inscription.statut != "ABANDONNE":
        messages.warning(request, "Seules les inscriptions abandonnées peuvent être reprises.")
        return redirect("inscriptions:mes_inscriptions")

    section = inscription.section_cours

    # Section encore ouverte ?
    if not section.est_ouverte:
        messages.error(
            request,
            f"La section {section.numero_section} de {section.cours.code} est fermée — reprise impossible.",
        )
        return redirect("inscriptions:mes_inscriptions")

    # Capacité encore disponible ?
    nb_inscrits = Inscription.objects.filter(section_cours=section, statut="INSCRIT").count()
    if section.capacite_max and nb_inscrits >= section.capacite_max:
        messages.error(
            request,
            f"La section {section.numero_section} de {section.cours.code} est complète — reprise impossible.",
        )
        return redirect("inscriptions:mes_inscriptions")

    # Déjà réinscrit à ce cours via une autre inscription active ?
    if Inscription.objects.filter(
        etudiant=request.user.profil_etudiant,
        section_cours__cours=section.cours,
        statut="INSCRIT",
    ).exclude(pk=inscription.pk).exists():
        messages.warning(
            request,
            f"Vous êtes déjà inscrit au cours {section.cours.code} via une autre section.",
        )
        return redirect("inscriptions:mes_inscriptions")

    HistoriqueInscription.objects.create(
        inscription=inscription,
        statut_precedent=inscription.statut,
        nouveau_statut="INSCRIT",
        modifie_par=request.user,
        raison="Reprise par l'étudiant",
    )

    inscription.statut = "INSCRIT"
    inscription.date_abandon = None
    inscription.save()

    messages.success(
        request,
        f"✓ Vous avez repris le cours {section.cours.code}-{section.numero_section}.",
    )
    return redirect("inscriptions:mes_inscriptions")

@login_required
@user_passes_test(est_etudiant)
def vue_mes_inscriptions(request):
    """Mes inscriptions (vue étudiant) — filtrées par période et statut."""
    etudiant = request.user.profil_etudiant

    # ── Périodes disponibles pour cet étudiant ──────────────────────────────
    periodes = (
        etudiant.inscriptions
        .values("section_cours__semestre", "section_cours__annee")
        .distinct()
        .order_by("-section_cours__annee", "section_cours__semestre")
    )

    # Période courante par défaut : la plus récente
    if periodes.exists():
        periode_defaut = periodes.first()
        semestre_defaut = periode_defaut["section_cours__semestre"]
        annee_defaut    = periode_defaut["section_cours__annee"]
    else:
        semestre_defaut = None
        annee_defaut    = None

    semestre_filtre = request.GET.get("semestre", semestre_defaut)
    annee_filtre    = request.GET.get("annee", annee_defaut)
    try:
        annee_filtre = int(annee_filtre) if annee_filtre else None
    except (ValueError, TypeError):
        annee_filtre = annee_defaut

    statut = request.GET.get("statut", "INSCRIT")

    # ── QuerySet de base filtré sur la période choisie ──────────────────────
    base_qs = etudiant.inscriptions.select_related(
        "section_cours__cours",
        "section_cours__professeur__utilisateur",
    )
    if semestre_filtre and annee_filtre:
        base_qs = base_qs.filter(
            section_cours__semestre=semestre_filtre,
            section_cours__annee=annee_filtre,
        )

    inscriptions = base_qs.filter(statut=statut).order_by("-date_inscription")

    # ── Statistiques (période courante uniquement) ───────────────────────────
    total_inscrit   = base_qs.filter(statut="INSCRIT").count()
    total_complete  = base_qs.filter(statut="COMPLETE").count()
    total_abandonne = base_qs.filter(statut="ABANDONNE").count()

    # ── Libellé des semestres pour l'affichage ───────────────────────────────
    SEMESTRE_LABELS = {"AUTOMNE": "Automne", "PRINTEMPS": "Printemps", "ETE": "Été"}

    periodes_display = [
        {
            "semestre": p["section_cours__semestre"],
            "annee":    p["section_cours__annee"],
            "label":    f"{SEMESTRE_LABELS.get(p['section_cours__semestre'], p['section_cours__semestre'])} {p['section_cours__annee']}",
            "actif":    p["section_cours__semestre"] == semestre_filtre and p["section_cours__annee"] == annee_filtre,
        }
        for p in periodes
    ]

    contexte = {
        "inscriptions":      inscriptions,
        "statut_actuel":     statut,
        "choix_statut":      Inscription.CHOIX_STATUT,
        "total_inscrit":     total_inscrit,
        "total_complete":    total_complete,
        "total_abandonne":   total_abandonne,
        "periodes_display":  periodes_display,
        "semestre_filtre":   semestre_filtre,
        "annee_filtre":      annee_filtre,
    }
    return render(request, "inscriptions/mes_inscriptions.html", contexte)

# ===========================================================================
# VUES ADMIN
# ===========================================================================


@login_required
@user_passes_test(est_administrateur)
def vue_liste_inscriptions(request):
    """Liste de toutes les inscriptions groupées par étudiant (admin)"""
    inscriptions_qs = Inscription.objects.select_related(
        "etudiant__utilisateur",
        "section_cours__cours",
        "section_cours__professeur__utilisateur",
    )

    # Filtres
    statut = request.GET.get("statut", "").strip()
    session = request.GET.get("session", "").strip()
    semestre = request.GET.get("semestre", "").strip()
    numero_etudiant = request.GET.get("numero_etudiant", "").strip()

    if statut:
        inscriptions_qs = inscriptions_qs.filter(statut=statut)
    if session:
        inscriptions_qs = inscriptions_qs.filter(section_cours__session=session)
    if semestre:
        inscriptions_qs = inscriptions_qs.filter(section_cours__semestre=semestre)
    if numero_etudiant:
        inscriptions_qs = inscriptions_qs.filter(
            etudiant__numero_etudiant__icontains=numero_etudiant
        )

    inscriptions_qs = inscriptions_qs.order_by("-date_inscription")
    toutes_inscriptions = list(inscriptions_qs)

    # Grouper par étudiant
    groupes = []
    etudiant_courant = None
    groupe_courant = []

    for inscription in toutes_inscriptions:
        num = inscription.etudiant.numero_etudiant
        if etudiant_courant != num:
            if groupe_courant:
                nb_inscrits = sum(1 for i in groupe_courant if i.statut == "INSCRIT")
                groupes.append(
                    {
                        "etudiant": groupe_courant[0].etudiant,
                        "inscriptions": groupe_courant,
                        "total": len(groupe_courant),
                        "nb_inscrits": nb_inscrits,
                    }
                )
            etudiant_courant = num
            groupe_courant = [inscription]
        else:
            groupe_courant.append(inscription)

    if groupe_courant:
        nb_inscrits = sum(1 for i in groupe_courant if i.statut == "INSCRIT")
        groupes.append(
            {
                "etudiant": groupe_courant[0].etudiant,
                "inscriptions": groupe_courant,
                "total": len(groupe_courant),
                "nb_inscrits": nb_inscrits,
            }
        )

    elements_par_page = getattr(settings, "ELEMENTS_PAR_PAGE", 20)
    paginateur = Paginator(groupes, elements_par_page)
    numero_page = request.GET.get("page", 1)
    page_obj = paginateur.get_page(numero_page)

    contexte = {
        "groupes": page_obj.object_list,
        "page_obj": page_obj,
        "choix_statut": Inscription.CHOIX_STATUT,
        "total_etudiants": len(groupes),
        "total_inscriptions": len(toutes_inscriptions),
    }
    return render(request, "inscriptions/liste_inscriptions.html", contexte)




@login_required
@user_passes_test(est_administrateur)
def vue_creer_inscription(request):
    """Créer une nouvelle inscription (admin)"""

    if request.method == "POST":
        id_etudiant  = request.POST.get("etudiant")
        ids_sections = request.POST.getlist("sections_selectionnees")

        if not id_etudiant or not ids_sections:
            messages.error(request, "Veuillez sélectionner un étudiant et au moins une section.")
            return redirect("inscriptions:creer_inscription")

        try:
            etudiant = Etudiant.objects.get(id=id_etudiant)
        except Etudiant.DoesNotExist:
            messages.error(request, "Étudiant introuvable.")
            return redirect("inscriptions:creer_inscription")

        nb_creees  = 0
        nb_erreurs = 0

        for id_section in ids_sections:
            try:
                section = SectionCours.objects.get(id=id_section)

                # Déjà inscrit à ce cours ?
                if Inscription.objects.filter(
                    etudiant=etudiant,
                    section_cours__cours=section.cours,
                    statut="INSCRIT",
                ).exists():
                    messages.warning(
                        request,
                        f"L'étudiant est déjà inscrit au cours {section.cours.code}.",
                    )
                    nb_erreurs += 1
                    continue

                # Maximum de cours par session
                max_cours  = getattr(settings, "MAX_COURS_PAR_SESSION", 7)
                nb_session = Inscription.objects.filter(
                    etudiant=etudiant,
                    section_cours__session=section.session,
                    section_cours__semestre=section.semestre,
                    section_cours__annee=section.annee,
                    statut="INSCRIT",
                ).count()

                if nb_session >= max_cours:
                    messages.error(
                        request,
                        f"Maximum de {max_cours} cours atteint pour cette session "
                        f"— {section.cours.code} non inscrit.",
                    )
                    nb_erreurs += 1
                    continue

                # Capacité de la section
                nb_inscrits = Inscription.objects.filter(
                    section_cours=section,
                    statut="INSCRIT",
                ).count()

                if section.capacite_max and nb_inscrits >= section.capacite_max:
                    messages.error(
                        request,
                        f"La section {section.numero_section} de {section.cours.code} est complète.",
                    )
                    nb_erreurs += 1
                    continue

                # Conflits d'horaire
                conflit = False
                inscriptions_meme_jour = Inscription.objects.filter(
                    etudiant=etudiant,
                    section_cours__session=section.session,
                    section_cours__semestre=section.semestre,
                    section_cours__annee=section.annee,
                    section_cours__jour_semaine=section.jour_semaine,
                    statut="INSCRIT",
                )

                for insc in inscriptions_meme_jour:
                    sect_existante = insc.section_cours
                    if sect_existante.conflit_horaire(
                        section.jour_semaine,
                        section.heure_debut,
                        section.heure_fin,
                    ):
                        messages.error(
                            request,
                            f"Conflit d'horaire : {section.cours.code} chevauche "
                            f"{sect_existante.cours.code}-{sect_existante.numero_section}.",
                        )
                        conflit = True
                        nb_erreurs += 1
                        break

                if conflit:
                    continue

                # Création
                nouvelle_inscription = Inscription(etudiant=etudiant, section_cours=section)
                nouvelle_inscription.full_clean()
                nouvelle_inscription.save()

                HistoriqueInscription.objects.create(
                    inscription=nouvelle_inscription,
                    statut_precedent="",
                    nouveau_statut="INSCRIT",
                    modifie_par=request.user,
                    raison=f"Inscription créée par {request.user.get_full_name()}",
                )
                nb_creees += 1

            except SectionCours.DoesNotExist:
                messages.error(request, f"Section {id_section} introuvable.")
                nb_erreurs += 1

            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for champ, erreurs in e.message_dict.items():
                        for erreur in erreurs:
                            messages.error(request, f"{section.cours.code} — {champ} : {erreur}")
                else:
                    for msg in e.messages:
                        messages.error(request, f"{section.cours.code} — {msg}")
                nb_erreurs += 1

            except Exception as e:
                messages.error(request, f"Erreur ({section.cours.code}) : {str(e)}")
                nb_erreurs += 1

        if nb_creees > 0:
            messages.success(
                request,
                f"✓ {nb_creees} inscription(s) créée(s) pour "
                f"{etudiant.utilisateur.get_full_name()}.",
            )
            return redirect("inscriptions:liste_inscriptions")

        return redirect("inscriptions:creer_inscription")

    # ── GET ───────────────────────────────────────────────────────────────────
    etudiants = (
        Etudiant.objects.filter(utilisateur__is_active=True)
        .select_related("utilisateur", "departement")
        .order_by("numero_etudiant")
    )

    sections = (
        SectionCours.objects.filter(est_ouverte=True)
        .select_related("cours__departement", "professeur__utilisateur")
        .order_by("cours__code", "numero_section")
    )

    sections_par_cours = defaultdict(list)
    for section in sections:
        sections_par_cours[section.cours].append(section)

    contexte = {
        "etudiants": etudiants,
        "sections_par_cours": dict(sections_par_cours),
        "choix_session": SectionCours.CHOIX_SESSION,
        "choix_semestre": SectionCours.CHOIX_SEMESTRE,
    }
    return render(request, "inscriptions/creer_inscription.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def sections_pour_etudiant(request, etudiant_id):
    """Vue AJAX — retourne les sections compatibles avec le profil de l'étudiant"""
    try:
        etudiant = Etudiant.objects.select_related(
            "utilisateur", "departement"
        ).get(id=etudiant_id)
    except Etudiant.DoesNotExist:
        return JsonResponse({"erreur": "Étudiant introuvable."}, status=404)

    sections = (
        SectionCours.objects.filter(
            est_ouverte=True,
            cours__departement=etudiant.departement,
            cours__niveau=etudiant.niveau,
        )
        .select_related("cours__departement", "professeur__utilisateur")
        .order_by("cours__code", "numero_section")
    )

    # Exclure les cours où l'étudiant est déjà inscrit
    deja_inscrits = Inscription.objects.filter(
        etudiant=etudiant,
        statut="INSCRIT",
    ).values_list("section_cours_id", flat=True)

    sections = sections.exclude(id__in=deja_inscrits)

    cours_data = {}
    for section in sections:
        code = section.cours.code
        if code not in cours_data:
            cours_data[code] = {
                "nom":      section.cours.nom,
                "credits":  section.cours.credits,
                "niveau":   section.cours.get_niveau_display(),
                "sections": [],
            }
        cours_data[code]["sections"].append({
            "id":           section.id,
            "numero":       section.numero_section,
            "jour":         section.get_jour_semaine_display(),
            "heure_debut":  section.heure_debut.strftime("%H:%M"),
            "heure_fin":    section.heure_fin.strftime("%H:%M"),
            "professeur":   section.professeur.utilisateur.get_full_name() if section.professeur else "",
            "session":      section.get_session_display(),
            "session_raw":  section.session,
            "semestre":     section.get_semestre_display(),
            "semestre_raw": section.semestre,
            "annee":        section.annee,
            "salle":        section.salle,
            "nb_inscrits":  section.nombre_inscrits(),
            "capacite_max": section.capacite_max,
        })

    return JsonResponse({
        "etudiant": {
            "nom":         etudiant.utilisateur.get_full_name(),
            "departement": etudiant.departement.nom if etudiant.departement else "—",
            "niveau":      etudiant.get_niveau_display(),
        },
        "cours": cours_data,
    })

@login_required
@user_passes_test(est_administrateur)
def vue_modifier_inscription(request, id_inscription):
    """Modifier une inscription existante (admin)"""
    inscription = get_object_or_404(
        Inscription.objects.select_related(
            "etudiant__utilisateur", "section_cours__cours"
        ),
        id=id_inscription,
    )

    if request.method == "POST":
        nouveau_statut = request.POST.get("statut")
        raison = request.POST.get("raison", "").strip()

        if not nouveau_statut:
            messages.error(request, "Veuillez sélectionner un statut.")
            return redirect(
                "inscriptions:modifier_inscription", id_inscription=id_inscription
            )

        if nouveau_statut not in dict(Inscription.CHOIX_STATUT):
            messages.error(request, "Statut invalide.")
            return redirect(
                "inscriptions:modifier_inscription", id_inscription=id_inscription
            )

        if nouveau_statut != inscription.statut:
            HistoriqueInscription.objects.create(
                inscription=inscription,
                statut_precedent=inscription.statut,
                nouveau_statut=nouveau_statut,
                modifie_par=request.user,
                raison=raison or f"Modifié par {request.user.get_full_name()}",
            )
            ancien_statut_affichage = inscription.get_statut_display()
            inscription.statut = nouveau_statut
            if nouveau_statut == "ABANDONNE":
                inscription.date_abandon = timezone.now()
            inscription.save()
            messages.success(
                request,
                f"Statut modifié de « {ancien_statut_affichage} » à « {inscription.get_statut_display()} ».",
            )
            return redirect("inscriptions:liste_inscriptions")
        else:
            messages.info(request, "Aucun changement détecté.")
            return redirect(
                "inscriptions:modifier_inscription", id_inscription=id_inscription
            )

    contexte = {
        "inscription": inscription,
        "choix_statut": Inscription.CHOIX_STATUT,
    }
    return render(request, "inscriptions/modifier_inscription.html", contexte)


@login_required
@user_passes_test(est_administrateur)
def vue_modifier_statut(request, id_inscription):
    """Modifier rapidement le statut d'une inscription (admin)"""
    inscription = get_object_or_404(Inscription, id=id_inscription)

    if request.method == "POST":
        nouveau_statut = request.POST.get("statut")
        raison = request.POST.get("raison", "")

        if nouveau_statut and nouveau_statut in dict(Inscription.CHOIX_STATUT):
            HistoriqueInscription.objects.create(
                inscription=inscription,
                statut_precedent=inscription.statut,
                nouveau_statut=nouveau_statut,
                modifie_par=request.user,
                raison=raison,
            )
            inscription.statut = nouveau_statut
            if nouveau_statut == "ABANDONNE":
                inscription.date_abandon = timezone.now()
            inscription.save()
            messages.success(request, "Statut d'inscription modifié.")
        else:
            messages.error(request, "Statut invalide.")

    return redirect("inscriptions:liste_inscriptions")


@login_required
@user_passes_test(est_administrateur)
def vue_supprimer_inscription(request, id_inscription):
    """Supprimer une inscription (admin)"""
    inscription = get_object_or_404(
        Inscription.objects.select_related(
            "etudiant__utilisateur", "section_cours__cours"
        ),
        id=id_inscription,
    )

    if request.method == "POST":
        nom_etudiant = inscription.etudiant.utilisateur.get_full_name()
        code_cours = inscription.section_cours.cours.code
        num_section = inscription.section_cours.numero_section

        HistoriqueInscription.objects.create(
            inscription=inscription,
            statut_precedent=inscription.statut,
            nouveau_statut="SUPPRIME",
            modifie_par=request.user,
            raison=f"Inscription supprimée par {request.user.get_full_name()}",
        )
        inscription.delete()
        messages.success(
            request,
            f"Inscription supprimée : {nom_etudiant} - {code_cours}-{num_section}",
        )
        return redirect("inscriptions:liste_inscriptions")

    contexte = {"inscription": inscription}
    return render(request, "inscriptions/supprimer_inscription.html", contexte)


@login_required
def vue_historique_inscription(request, id_inscription):
    """Historique d'une inscription"""
    inscription = get_object_or_404(Inscription, id=id_inscription)

    peut_voir = request.user.est_administrateur() or (
        request.user.est_etudiant()
        and inscription.etudiant == request.user.profil_etudiant
    )

    if not peut_voir:
        messages.error(request, "Vous n'avez pas la permission de voir cet historique.")
        return redirect("accueil")

    historique = inscription.historique.select_related("modifie_par").order_by(
        "-modifie_le"
    )

    contexte = {
        "inscription": inscription,
        "historique": historique,
    }
    return render(request, "inscriptions/historique_inscriptions.html", contexte)