# admin.py

from django.contrib import admin
from .models import SiteSettings, NewsletterInscription, Livre, Personnel, Examen

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identité",  {'fields': ('nom_etablissement', 'nom_complet', 'slogan', 'annee_fondation')}),
        ("Contact",   {'fields': ('adresse_ligne1', 'telephone', 'email')}),
        ("Réseaux",   {'fields': ('lien_twitter', 'lien_facebook', 'lien_linkedin')}),
        ("Copyright", {'fields': ('annee_copyright',)}),
    )

    def has_add_permission(self, request):
        # Empêche de créer plusieurs instances (singleton)
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'auteur', 'annee', 'disponible']
    list_filter   = ['disponible']
    search_fields = ['titre', 'auteur']

@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'poste']
    list_filter   = ['poste']
    search_fields = ['nom']

@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'date', 'statut']
    list_filter   = ['statut']
    search_fields = ['titre']
    readonly_fields = ['statut']  # calculé automatiquement dans save()


@admin.register(NewsletterInscription)
class NewsletterInscriptionAdmin(admin.ModelAdmin):
    list_display  = ['email', 'nom', 'inscrit_le']
    search_fields = ['email', 'nom']
    ordering      = ['-inscrit_le']