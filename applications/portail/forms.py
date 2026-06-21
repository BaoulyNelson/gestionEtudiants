from django import forms
from .models import Examen, SiteSettings

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
        
        
        
# portail/forms.py




class ExamenForm(forms.ModelForm):
    class Meta:
        model  = Examen
        fields = ['titre', 'date', 'description']
        # statut est exclu : recalculé automatiquement par Examen.save()

        widgets = {
            'titre': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': "Ex : Examen final de Psychologie Clinique",
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': "Instructions, matières couvertes, documents autorisés…",
            }),
        }

        labels = {
            'titre':       "Intitulé de l'examen",
            'date':        "Date de l'examen",
            'description': "Description / Instructions",
        }