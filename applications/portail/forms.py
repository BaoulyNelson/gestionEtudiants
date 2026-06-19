from django import forms
from .models import SiteSettings

class FormulaireParametresSite(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "nom_etablissement", "nom_complet", "slogan", "annee_fondation",
            "adresse_ligne1", "telephone", "email",
            "logo", "logo_small",
            "nom_directeur_etudes", "titre_directeur_etudes",
            "signature_directeur", "cachet_officiel",
            "lien_twitter", "lien_facebook", "lien_linkedin",
            "annee_copyright",
        ]
        widgets = {
            "nom_etablissement": forms.TextInput(attrs={"class": "form-control"}),
            "nom_complet":       forms.TextInput(attrs={"class": "form-control"}),
            "slogan":            forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "annee_fondation":   forms.NumberInput(attrs={"class": "form-control"}),
            "adresse_ligne1":    forms.TextInput(attrs={"class": "form-control"}),
            "telephone":         forms.TextInput(attrs={"class": "form-control"}),
            "email":             forms.EmailInput(attrs={"class": "form-control"}),
            "nom_directeur_etudes":   forms.TextInput(attrs={"class": "form-control"}),
            "titre_directeur_etudes": forms.TextInput(attrs={"class": "form-control"}),
            "logo":                   forms.FileInput(attrs={"class": "form-control"}),
            "logo_small":             forms.FileInput(attrs={"class": "form-control"}),
            "signature_directeur":    forms.FileInput(attrs={"class": "form-control"}),
            "cachet_officiel":        forms.FileInput(attrs={"class": "form-control"}),
            "lien_twitter":      forms.URLInput(attrs={"class": "form-control"}),
            "lien_facebook":     forms.URLInput(attrs={"class": "form-control"}),
            "lien_linkedin":     forms.URLInput(attrs={"class": "form-control"}),
            "annee_copyright":   forms.NumberInput(attrs={"class": "form-control"}),
        }