from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Utilisateur, Etudiant, Professeur, Administrateur


# 🧩 1. Définir les actions
@admin.action(description="Définir le genre sur Masculin")
def set_gender_masculin(modeladmin, request, queryset):
    queryset.update(genre="M")


@admin.action(description="Définir le genre sur Féminin")
def set_gender_feminin(modeladmin, request, queryset):
    queryset.update(genre="F")


@admin.action(description="Rôle éditorial → Lecteur")
def set_role_editorial_lecteur(modeladmin, request, queryset):
    queryset.update(role_editorial="LECTEUR")


@admin.action(description="Rôle éditorial → Auteur")
def set_role_editorial_auteur(modeladmin, request, queryset):
    queryset.update(role_editorial="AUTEUR")


@admin.action(description="Rôle éditorial → Éditeur")
def set_role_editorial_editeur(modeladmin, request, queryset):
    queryset.update(role_editorial="EDITEUR")


# 🧩 2. Étendre ton UserAdmin existant
@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "role_editorial",
        "genre",
        "numero_telephone",
        "is_active",
        "cree_le",
    ]
    list_filter = ["role", "role_editorial", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name", "numero_telephone"]
    ordering = ["-cree_le"]
    actions = [
        set_gender_masculin,
        set_gender_feminin,
        set_role_editorial_lecteur,
        set_role_editorial_auteur,
        set_role_editorial_editeur,
    ]

    fieldsets = (
        ("Informations de connexion", {"fields": ("email", "password")}),
        (
            "Informations personnelles",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "genre",
                    "numero_telephone",
                    "adresse",
                    "date_naissance",
                    "photo_profil",
                )
            },
        ),
        (
            "Rôle et permissions",
            {
                "fields": (
                    "role",
                    "role_editorial",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "doit_changer_mot_de_passe",
                )
            },
        ),
        (
            "Dates importantes",
            {
                "fields": ("last_login", "cree_le", "modifie_le"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "role_editorial",
                    "genre",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ["cree_le", "modifie_le", "last_login"]


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = [
        "numero_etudiant",
        "get_full_name",
        "departement",
        "niveau",
        "date_inscription",
    ]
    list_filter = ["departement", "niveau"]
    search_fields = [
        "numero_etudiant",
        "utilisateur__first_name",
        "utilisateur__last_name",
    ]
    raw_id_fields = ["utilisateur"]

    def get_full_name(self, obj):
        return obj.utilisateur.get_full_name()

    get_full_name.short_description = "Nom complet"


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = [
        "identifiant_professeur",
        "get_full_name",
        "departement",
        "specialite",
        "date_embauche",
    ]
    list_filter = ["departement"]
    search_fields = [
        "identifiant_professeur",
        "utilisateur__first_name",
        "utilisateur__last_name",
        "specialite",
    ]
    raw_id_fields = ["utilisateur"]

    def get_full_name(self, obj):
        return obj.utilisateur.get_full_name()

    get_full_name.short_description = "Nom complet"


@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ["identifiant_administrateur", "get_full_name", "poste"]
    search_fields = [
        "identifiant_administrateur",
        "utilisateur__first_name",
        "utilisateur__last_name",
        "poste",
    ]
    raw_id_fields = ["utilisateur"]

    def get_full_name(self, obj):
        return obj.utilisateur.get_full_name()

    get_full_name.short_description = "Nom complet"