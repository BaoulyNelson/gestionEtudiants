from django.contrib import admin
from .models import Candidature, Statistique, Ambassadeur, FAQ, TypeBourse, VisiteVirtuelle
from departments.models import Department

@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ['prenom', 'nom', 'email', 'programme', 'statut', 'date_creation']
    list_filter = ['statut', 'programme', 'date_creation']
    search_fields = ['prenom', 'nom', 'email']
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'email', 'telephone')
        }),
        ('Candidature', {
            'fields': ('programme', 'lettre_motivation', 'accepte_conditions')
        }),
        ('Statut', {
            'fields': ('statut', 'date_creation', 'date_modification')
        }),
    )
    
    


@admin.register(Statistique)
class StatistiqueAdmin(admin.ModelAdmin):
    list_display = ['valeur', 'label', 'couleur', 'ordre', 'actif']
    list_filter = ['couleur', 'actif']
    list_editable = ['ordre', 'actif']


@admin.register(Ambassadeur)
class AmbassadeurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'programme', 'annee', 'ordre', 'actif']
    list_filter = ['programme', 'actif']
    list_editable = ['ordre', 'actif']
    search_fields = ['nom', 'programme']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'categorie', 'ordre', 'actif', 'nombre_vues']
    list_filter = ['categorie', 'actif']
    list_editable = ['ordre', 'actif']
    search_fields = ['question', 'reponse']





@admin.register(TypeBourse)
class TypeBourseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'pourcentage', 'nombre_disponible', 'actif']
    list_filter = ['actif', 'pourcentage']
    list_editable = ['nombre_disponible', 'actif']


@admin.register(VisiteVirtuelle)
class VisiteVirtuelleAdmin(admin.ModelAdmin):
    list_display = ['titre', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']