from django.contrib import admin
from django.utils.html import format_html
from .models import Departement


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display  = ['code', 'nom', 'affichage_chef', 'nombre_etudiants', 'nombre_professeurs']
    search_fields = ['code', 'nom']
    list_filter   = ['code']
    raw_id_fields = ['chef_departement']

    fieldsets = (
        ('📚 Informations principales', {
            'fields': ('code', 'nom', 'description'),
        }),
        ('👔 Gestion', {
            'fields': ('chef_departement',),
        }),
    )

    def affichage_chef(self, obj):
        """Affiche le nom complet du chef de département, ou un libellé si non assigné"""
        if obj.chef_departement:
            return obj.chef_departement.user.get_full_name()
        return format_html('<span style="color: gray;">Non assigné</span>')
    affichage_chef.short_description = 'Chef de département'

    def nombre_etudiants(self, obj):
        """Affiche le nombre d'étudiants avec une pastille colorée"""
        total = obj.obtenir_total_etudiants()
        return format_html(
            '<span style="background-color: #17a2b8; color: white;'
            ' padding: 3px 10px; border-radius: 3px;">{} étudiant(s)</span>',
            total,
        )
    nombre_etudiants.short_description = 'Étudiants'

    def nombre_professeurs(self, obj):
        """Affiche le nombre de professeurs avec une pastille colorée"""
        total = obj.obtenir_total_professeurs()
        return format_html(
            '<span style="background-color: #6c757d; color: white;'
            ' padding: 3px 10px; border-radius: 3px;">{} prof(s)</span>',
            total,
        )
    nombre_professeurs.short_description = 'Professeurs'