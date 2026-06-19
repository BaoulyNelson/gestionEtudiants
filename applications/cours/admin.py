from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Cours, Prerequis, SectionCours


# ── Formulaire pour l'action rapide ─────────────────────────────────────────
class FormulaireCreerSection(forms.Form):
    numero_section = forms.CharField(label="Numéro de section", initial="A")
    jour_semaine = forms.ChoiceField(
        choices=SectionCours.CHOIX_JOUR, label="Jour de la semaine"
    )
    heure_debut = forms.TimeField(label="Heure de début", initial="08:00")
    heure_fin = forms.TimeField(label="Heure de fin", initial="10:00")
    salle = forms.CharField(label="Salle", required=False)
    session = forms.ChoiceField(choices=SectionCours.CHOIX_SESSION, label="Session")
    semestre = forms.ChoiceField(choices=SectionCours.CHOIX_SEMESTRE, label="Semestre")
    annee = forms.IntegerField(label="Année académique", initial=2025)
    capacite = forms.IntegerField(label="Capacité maximale", initial=30)


# ── Admin : Cours ────────────────────────────────────────────────────────────
@admin.register(Cours)
class AdminCours(admin.ModelAdmin):
    list_display = [
        "code",
        "nom",
        "departement",
        "badge_credits",
        "badge_annee",
        "nombre_sections",
        "affiche_actif",
    ]
    list_filter = ["departement", "niveau", "est_actif", "cree_le"]
    search_fields = ["code", "nom", "niveau"]
    ordering = ["code"]
    list_per_page = 20

    fieldsets = (
        (
            "📖 Informations principales",
            {
                "fields": ("code", "nom", "description", "credits"),
            },
        ),
        (
            "🏛️ Classification",
            {
                "fields": ("departement", "niveau"),
            },
        ),
        (
            "⚙️ Statut",
            {
                "fields": ("est_actif",),
            },
        ),
    )

    actions = [
        "activer_cours",
        "desactiver_cours",
        "dupliquer_cours",
        "creer_section_globale",
    ]

    # ── Colonnes d'affichage ─────────────────────────────────────────────────

    def badge_credits(self, obj):
        return format_html(
            '<span style="background:#ffc107;color:black;padding:3px 10px;border-radius:3px;">'
            "{} crédit(s)</span>",
            obj.credits,
        )

    badge_credits.short_description = "Crédits"

    def badge_annee(self, obj):
        return format_html(
            '<span style="background:#007bff;color:white;padding:3px 10px;border-radius:3px;">'
            "Année {}</span>",
            obj.niveau,
        )

    badge_annee.short_description = "Année"

    def nombre_sections(self, obj):
        total = obj.sections.count()
        return format_html(
            '<span style="background:#28a745;color:white;padding:3px 10px;border-radius:3px;">'
            "{} section(s)</span>",
            total,
        )

    nombre_sections.short_description = "Sections"

    def affiche_actif(self, obj):
        if obj.est_actif:
            return format_html('<span style="color:green;font-size:18px;">✓</span>')
        return format_html('<span style="color:red;font-size:18px;">✗</span>')

    affiche_actif.short_description = "Actif"

    # ── Actions ──────────────────────────────────────────────────────────────

    def activer_cours(self, request, queryset):
        nb = queryset.update(est_actif=True)
        self.message_user(request, f"{nb} cours activé(s).")

    activer_cours.short_description = "✓ Activer les cours"

    def desactiver_cours(self, request, queryset):
        nb = queryset.update(est_actif=False)
        self.message_user(request, f"{nb} cours désactivé(s).")

    desactiver_cours.short_description = "✗ Désactiver les cours"

    def dupliquer_cours(self, request, queryset):
        nb = 0
        for cours in queryset:
            nouveau_code = f"{cours.code}_COPIE"
            if not Cours.objects.filter(code=nouveau_code).exists():
                cours.pk = None
                cours.code = nouveau_code
                cours.save()
                nb += 1
        self.message_user(request, f"{nb} cours dupliqué(s).")

    dupliquer_cours.short_description = "📋 Dupliquer les cours sélectionnés"

    def creer_section_globale(self, request, queryset):
        nb = 0
        for cours in queryset:
            if not SectionCours.objects.filter(
                cours=cours, numero_section="G"
            ).exists():
                SectionCours.objects.create(
                    cours=cours,
                    numero_section="G",
                    professeur=None,
                    jour_semaine="LUNDI",
                    heure_debut="07:00:00",
                    heure_fin="10:00:00",
                    session="SESSION_2",
                    semestre="AUTOMNE",
                    annee=2025,
                    capacite_max=30,
                    est_ouverte=True,
                )
                nb += 1
        self.message_user(request, f"{nb} section(s) globale(s) créée(s).")

    creer_section_globale.short_description = (
        "➕ Créer une section globale pour les cours sélectionnés"
    )

    # ── Filtrage spécial prépa ────────────────────────────────────────────────

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get("niveau__exact") == "1":
            qs = qs.filter(departement__isnull=True)
        return qs


# ── Admin : Sections ─────────────────────────────────────────────────────────
@admin.register(SectionCours)
class AdminSection(admin.ModelAdmin):
    list_display = [
        "affiche_section",
        "cours",
        "nom_professeur",
        "affiche_horaire",
        "badge_periode",
        "statut_inscriptions",
        "affiche_ouvert",
    ]
    list_filter = [
        "session",
        "semestre",
        "annee",
        "jour_semaine",
        "est_ouverte",
        "cours__departement",
        "cours__niveau",
    ]
    search_fields = [
        "cours__code",
        "cours__nom",
        "numero_section",
        "professeur__utilisateur__last_name",
    ]
    raw_id_fields = ["cours", "professeur"]
    ordering = ["cours__code", "numero_section"]
    list_per_page = 20

    fieldsets = (
        ("📚 Cours", {"fields": ("cours", "numero_section", "professeur")}),
        (
            "🕐 Horaire",
            {"fields": ("jour_semaine", "heure_debut", "heure_fin", "salle")},
        ),
        ("📅 Période académique", {"fields": ("session", "semestre", "annee")}),
        ("👥 Capacité et statut", {"fields": ("capacite_max", "est_ouverte")}),
    )

    actions = ["ouvrir_sections", "fermer_sections", "augmenter_capacite"]

    # ── Colonnes d'affichage ─────────────────────────────────────────────────

    def affiche_section(self, obj):
        return f"{obj.cours.code}-{obj.numero_section}"

    affiche_section.short_description = "Section"

    def nom_professeur(self, obj):
        if obj.professeur:
            return obj.professeur.utilisateur.get_full_name()
        return format_html('<span style="color:red;">Non assigné</span>')

    nom_professeur.short_description = "Professeur"

    def affiche_horaire(self, obj):
        return format_html(
            "<strong>{}</strong><br>{} – {}",
            obj.get_jour_semaine_display(),
            obj.heure_debut.strftime("%H:%M"),
            obj.heure_fin.strftime("%H:%M"),
        )

    affiche_horaire.short_description = "Horaire"

    def badge_periode(self, obj):
        return format_html(
            '<span style="background:#6610f2;color:white;padding:3px 10px;border-radius:3px;">'
            "{} {}</span>",
            obj.get_semestre_display(),
            obj.annee,
        )

    badge_periode.short_description = "Période"

    def statut_inscriptions(self, obj):
        inscrits = obj.nombre_inscrits()
        capacite = obj.capacite_max
        pourcentage = (inscrits / capacite * 100) if capacite > 0 else 0
        couleur = (
            "red" if pourcentage >= 90 else ("orange" if pourcentage >= 70 else "green")
        )
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;">'
            "{}/{}</span>",
            couleur,
            inscrits,
            capacite,
        )

    statut_inscriptions.short_description = "Inscriptions"

    def affiche_ouvert(self, obj):
        if obj.est_ouverte:
            return format_html(
                '<span style="color:green;font-size:18px;">🟢 Ouvert</span>'
            )
        return format_html('<span style="color:red;font-size:18px;">🔴 Fermé</span>')

    affiche_ouvert.short_description = "Statut"

    # ── Actions ──────────────────────────────────────────────────────────────

    def ouvrir_sections(self, request, queryset):
        nb = queryset.update(est_ouverte=True)
        self.message_user(request, f"{nb} section(s) ouverte(s).")

    ouvrir_sections.short_description = "🟢 Ouvrir aux inscriptions"

    def fermer_sections(self, request, queryset):
        nb = queryset.update(est_ouverte=False)
        self.message_user(request, f"{nb} section(s) fermée(s).")

    fermer_sections.short_description = "🔴 Fermer aux inscriptions"

    def augmenter_capacite(self, request, queryset):
        for section in queryset:
            section.capacite_max += 5
            section.save()
        self.message_user(
            request,
            f"Capacité augmentée de 5 places pour {queryset.count()} section(s).",
        )

    augmenter_capacite.short_description = "➕ Augmenter la capacité (+5)"


# ── Admin : Prérequis ────────────────────────────────────────────────────────
@admin.register(Prerequis)
class AdminPrerequis(admin.ModelAdmin):
    list_display = ["cours", "cours_prerequis"]
    search_fields = ["cours__code", "cours_prerequis__code"]
    raw_id_fields = ["cours", "cours_prerequis"]
