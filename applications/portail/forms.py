from django import forms
from .models import Examen, SiteSettings
from applications.cours.models import SectionCours


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
            "nom_etablissement":      forms.TextInput(attrs={"class": "form-control"}),
            "nom_complet":            forms.TextInput(attrs={"class": "form-control"}),
            "slogan":                 forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "annee_fondation":        forms.NumberInput(attrs={"class": "form-control"}),
            "adresse_ligne1":         forms.TextInput(attrs={"class": "form-control"}),
            "telephone":              forms.TextInput(attrs={"class": "form-control"}),
            "email":                  forms.EmailInput(attrs={"class": "form-control"}),
            "nom_directeur_etudes":   forms.TextInput(attrs={"class": "form-control"}),
            "titre_directeur_etudes": forms.TextInput(attrs={"class": "form-control"}),
            "logo":                   forms.FileInput(attrs={"class": "form-control"}),
            "logo_small":             forms.FileInput(attrs={"class": "form-control"}),
            "signature_directeur":    forms.FileInput(attrs={"class": "form-control"}),
            "cachet_officiel":        forms.FileInput(attrs={"class": "form-control"}),
            "lien_twitter":           forms.URLInput(attrs={"class": "form-control"}),
            "lien_facebook":          forms.URLInput(attrs={"class": "form-control"}),
            "lien_linkedin":          forms.URLInput(attrs={"class": "form-control"}),
            "annee_copyright":        forms.NumberInput(attrs={"class": "form-control"}),
        }


class ExamenForm(forms.ModelForm):
    """
    Formulaire de création/modification d'un examen.
    Le queryset de section_cours est filtré selon le rôle :
    - Admin/superuser : toutes les sections
    - Professeur      : ses sections uniquement
    """

    class Meta:
        model  = Examen
        fields = ['section_cours', 'type_examen', 'date', 'heure', 'salle', 'duree_minutes', 'description']
        # statut est exclu : recalculé automatiquement par Examen.save()

        widgets = {
            'section_cours': forms.Select(attrs={
                'class': 'form-select',
            }),
            'type_examen': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',
            }),
            'heure': forms.TimeInput(attrs={
                'class': 'form-control',
                'type':  'time',
            }),
            'salle': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Ex : Salle A-101',
            }),
            'duree_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   '15',
                'step':  '15',
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': 'Instructions, documents autorisés, chapitres couverts…',
            }),
        }

        labels = {
            'section_cours':  'Section de cours',
            'type_examen':    "Type d'examen",
            'date':           "Date",
            'heure':          "Heure de début",
            'salle':          "Salle",
            'duree_minutes':  "Durée (minutes)",
            'description':    "Remarques / Instructions",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Filtrage du queryset selon le rôle
        if user is not None and not user.is_superuser and not user.est_administrateur():
            if user.est_professeur():
                self.fields['section_cours'].queryset = (
                    user.profil_professeur.sections_cours
                    .select_related('cours', 'cours__departement')
                    .order_by('cours__code', 'numero_section')
                )
            else:
                self.fields['section_cours'].queryset = SectionCours.objects.none()
        else:
            self.fields['section_cours'].queryset = (
                SectionCours.objects
                .select_related('cours', 'cours__departement', 'professeur__utilisateur')
                .order_by('cours__departement__nom', 'cours__code', 'numero_section')
            )

        # Libellé lisible pour chaque section
        self.fields['section_cours'].label_from_instance = lambda s: (
            f"{s.cours.code} — {s.cours.nom} "
            f"| Section {s.numero_section} "
            f"| {s.get_semestre_display()} {s.annee}"
        )
        
        
from django import forms
from .models import Personnel, Livre


class FormulairePersonnel(forms.ModelForm):
    class Meta:
        model = Personnel
        fields = ["poste", "departement", "nom", "description", "photo"]
        widgets = {
            "poste":        forms.Select(attrs={"class": "form-select", "id": "id_poste"}),
            "departement":  forms.Select(attrs={"class": "form-select", "id": "id_departement"}),
            "nom":          forms.TextInput(attrs={"class": "form-control"}),
            "description":  forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "photo":        forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # departement n'est pas obligatoire au niveau du form —
        # la validation métier est dans Personnel.clean()
        self.fields["departement"].required = False
        self.fields["departement"].empty_label = "— Sélectionner un département —"
        self.fields["photo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        # Déclenche le clean() du modèle pour valider la règle chef_dept ↔ departement
        instance = self.instance
        for field, value in cleaned_data.items():
            setattr(instance, field, value)
        try:
            instance.clean()
        except forms.ValidationError as e:
            self._update_errors(e)
        return cleaned_data


class FormulaireliVre(forms.ModelForm):
    class Meta:
        model  = Livre
        fields = ["titre", "auteur", "annee", "resume", "disponible"]
        widgets = {
            "titre":      forms.TextInput(attrs={"class": "form-control"}),
            "auteur":     forms.TextInput(attrs={"class": "form-control"}),
            "annee":      forms.NumberInput(attrs={"class": "form-control"}),
            "resume":     forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }