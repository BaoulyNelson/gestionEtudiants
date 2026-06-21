from django.contrib import admin
from .models import Article, Categorie, Tag


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "nombre_articles", "ordre")
    prepopulated_fields = {"slug": ("nom",)}
    list_editable = ("ordre",)
    search_fields = ("nom",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug")
    prepopulated_fields = {"slug": ("nom",)}
    search_fields = ("nom",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "titre",
        "auteur",
        "categorie",
        "statut",
        "est_a_la_une",
        "nombre_vues",
        "publie_le",
    )
    list_filter = ("statut", "categorie", "est_a_la_une", "est_breaking")
    search_fields = (
        "titre",
        "contenu",
        "auteur__email",
        "auteur__first_name",
        "auteur__last_name",
    )
    prepopulated_fields = {"slug": ("titre",)}
    date_hierarchy = "publie_le"
    list_editable = ("statut", "est_a_la_une")
    filter_horizontal = ("tags",)
    readonly_fields = ("nombre_vues", "cree_le", "modifie_le")


from django.contrib import admin
from django.utils import timezone
from .models import Evenement, Annonce


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = (
        "titre",
        "lieu",
        "date_debut",
        "date_fin",
        "statut_affiche",
        "date_creation",
    )
    list_filter = ("date_debut",)
    search_fields = ("titre", "description", "lieu")
    prepopulated_fields = {"slug": ("titre",)}
    date_hierarchy = "date_debut"
    ordering = ("-date_debut",)

    def statut_affiche(self, obj):
        return obj.get_statut()

    statut_affiche.short_description = "Statut"


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = (
        "titre",
        "organisateur",
        "lieu",
        "date_evenement",
        "date_publication",
        "est_active",
    )
    list_filter = ("est_active",)
    search_fields = ("titre", "contenu", "organisateur", "lieu")
    prepopulated_fields = {"slug": ("titre",)}
    date_hierarchy = "date_publication"
    list_editable = ("est_active",)
    ordering = ("-date_publication",)