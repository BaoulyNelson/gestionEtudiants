from django import forms
from .models import Cours, SectionCours, Prerequis


class FormulaireCours(forms.ModelForm):
    """Création / modification d'un cours"""

    class Meta:
        model = Cours
        fields = [
            "code",
            "nom",
            "description",
            "credits",
            "departement",
            "niveau",
            "est_actif",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "credits": forms.NumberInput(attrs={"class": "form-control"}),
            "departement": forms.Select(attrs={"class": "form-select"}),
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class FormulaireSection(forms.ModelForm):
    """Création / modification d'une section de cours"""

    class Meta:
        model = SectionCours
        fields = [
            "cours",
            "numero_section",
            "professeur",
            "jour_semaine",
            "heure_debut",
            "heure_fin",
            "salle",
            "session",
            "semestre",
            "annee",
            "capacite_max",
            "est_ouverte",
        ]
        widgets = {
            "cours": forms.Select(attrs={"class": "form-select"}),
            "numero_section": forms.TextInput(attrs={"class": "form-control"}),
            "professeur": forms.Select(attrs={"class": "form-select"}),
            "jour_semaine": forms.Select(attrs={"class": "form-select"}),
            "heure_debut": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "heure_fin": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "salle": forms.TextInput(attrs={"class": "form-control"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "semestre": forms.Select(attrs={"class": "form-select"}),
            "annee": forms.NumberInput(attrs={"class": "form-control"}),
            "capacite_max": forms.NumberInput(attrs={"class": "form-control"}),
            "est_ouverte": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class FormulairePrerequis(forms.ModelForm):
    """Ajout d'un prérequis à un cours"""

    class Meta:
        model = Prerequis
        fields = ["cours", "cours_prerequis"]
        widgets = {
            "cours": forms.Select(attrs={"class": "form-select"}),
            "cours_prerequis": forms.Select(attrs={"class": "form-select"}),
        }
