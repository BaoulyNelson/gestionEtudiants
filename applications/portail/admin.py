# admin.py

from django.contrib import admin
from .models import SiteSettings

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