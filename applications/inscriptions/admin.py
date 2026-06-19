from django.contrib import admin
from django.utils.html import format_html
from .models import Inscription, HistoriqueInscription


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ['affiche_etudiant', 'affiche_section_cours', 'badge_statut',
                    'date_inscription', 'actions_rapides']
    list_filter = ['statut', 'section_cours__session', 'section_cours__semestre',
                   'section_cours__annee', 'date_inscription']
    search_fields = ['etudiant__numero_etudiant', 'etudiant__utilisateur__first_name',
                     'etudiant__utilisateur__last_name', 'section_cours__cours__code']
    raw_id_fields = ['etudiant', 'section_cours']
    date_hierarchy = 'date_inscription'
    ordering = ['-date_inscription']
    list_per_page = 20

    fieldsets = (
        ('📝 Inscription', {
            'fields': ('etudiant', 'section_cours', 'statut')
        }),
        ('📅 Dates', {
            'fields': ('date_inscription', 'date_abandon')
        }),
    )

    readonly_fields = ['date_inscription']

    actions = ['marquer_complete', 'marquer_abandonne']

    def affiche_etudiant(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.etudiant.numero_etudiant,
            obj.etudiant.utilisateur.get_full_name()
        )
    affiche_etudiant.short_description = 'Étudiant'

    def affiche_section_cours(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>Section {}</small>',
            obj.section_cours.cours.code,
            obj.section_cours.numero_section
        )
    affiche_section_cours.short_description = 'Cours'

    def badge_statut(self, obj):
        couleurs = {
            'INSCRIT':   'green',
            'ABANDONNE': 'red',
            'COMPLETE':  'blue',
            'ECHOUE':    'darkred',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            couleurs.get(obj.statut, 'gray'),
            obj.get_statut_display()
        )
    badge_statut.short_description = 'Statut'

    def actions_rapides(self, obj):
        return format_html(
            '<a class="button" href="/admin/notes/note/add/?inscription={}">➕ Ajouter note</a>',
            obj.id
        )
    actions_rapides.short_description = 'Actions'

    def marquer_complete(self, request, queryset):
        nb = queryset.update(statut='COMPLETE')
        self.message_user(request, f'{nb} inscription(s) marquée(s) comme complétée(s).')
    marquer_complete.short_description = "✓ Marquer comme complété"

    def marquer_abandonne(self, request, queryset):
        from django.utils import timezone
        for inscription in queryset:
            inscription.statut      = 'ABANDONNE'
            inscription.date_abandon = timezone.now()
            inscription.save()
        self.message_user(request, f'{queryset.count()} inscription(s) abandonnée(s).')
    marquer_abandonne.short_description = "✗ Marquer comme abandonné"


@admin.register(HistoriqueInscription)
class HistoriqueInscriptionAdmin(admin.ModelAdmin):
    list_display  = ['inscription', 'statut_precedent', 'nouveau_statut', 'modifie_par', 'modifie_le']
    list_filter   = ['statut_precedent', 'nouveau_statut', 'modifie_le']
    search_fields = ['inscription__etudiant__numero_etudiant']
    raw_id_fields = ['inscription', 'modifie_par']
    date_hierarchy = 'modifie_le'
    ordering      = ['-modifie_le']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False