from django.contrib import admin
from .models import Devoir, FichierDevoir, Remise, FichierRemise


class FichierDevoirInline(admin.TabularInline):
    model           = FichierDevoir
    extra           = 1
    fields          = ['nom', 'fichier']
    verbose_name    = "Fichier joint"
    verbose_name_plural = "Fichiers joints"


class FichierRemiseInline(admin.TabularInline):
    model           = FichierRemise
    extra           = 0
    readonly_fields = ['nom', 'taille', 'ajoute_le']
    fields          = ['nom', 'fichier', 'taille', 'ajoute_le']
    can_delete      = False
    verbose_name    = "Fichier soumis"
    verbose_name_plural = "Fichiers soumis"


class RemiseInline(admin.TabularInline):
    model           = Remise
    extra           = 0
    readonly_fields = ['etudiant', 'statut', 'remis_le']
    fields          = ['etudiant', 'statut', 'note', 'commentaire_prof', 'remis_le']
    show_change_link = True


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display   = ['titre', 'section_cours', 'type_devoir', 'date_limite', 'est_publie', 'cree_par', 'cree_le']
    list_filter    = ['type_devoir', 'est_publie', 'section_cours__cours__departement']
    search_fields  = ['titre', 'section_cours__cours__nom', 'cree_par__last_name']
    list_editable  = ['est_publie']
    date_hierarchy = 'date_limite'
    inlines        = [FichierDevoirInline, RemiseInline]
    readonly_fields = ['cree_le', 'cree_par']

    fieldsets = (
        (None, {
            'fields': ('section_cours', 'titre', 'description', 'consignes', 'type_devoir'),
        }),
        ('Dates', {
            'fields': ('date_publication', 'date_limite'),
        }),
        ('Paramètres', {
            'fields': ('points_max', 'est_publie'),
        }),
        ('Métadonnées', {
            'fields': ('cree_par', 'cree_le'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Remise)
class RemiseAdmin(admin.ModelAdmin):
    list_display   = ['etudiant', 'devoir', 'statut', 'note', 'remis_le', 'modifie_le']
    list_filter    = ['statut', 'devoir__section_cours__cours__departement']
    search_fields  = ['etudiant__utilisateur__last_name', 'devoir__titre']
    readonly_fields = ['remis_le', 'modifie_le']
    inlines        = [FichierRemiseInline]

    fieldsets = (
        (None, {
            'fields': ('devoir', 'etudiant', 'statut', 'contenu'),
        }),
        ('Évaluation', {
            'fields': ('note', 'commentaire_prof'),
        }),
        ('Dates', {
            'fields': ('remis_le', 'modifie_le'),
            'classes': ('collapse',),
        }),
    )


@admin.register(FichierDevoir)
class FichierDevoirAdmin(admin.ModelAdmin):
    list_display = ['nom', 'devoir', 'cree_le']
    search_fields = ['nom', 'devoir__titre']
