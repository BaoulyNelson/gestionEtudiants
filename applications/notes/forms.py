from django import forms
from .models import Note
from applications.inscriptions.models import Inscription   # ← corrigé (était Enrollment)


class FormulaireNote(forms.ModelForm):
    """Formulaire unique pour la création et la modification d'une note"""

    class Meta:
        model = Note
        fields = [
            'inscription',
            'examen_mi_parcours',
            'examen_final',
            'travaux',
            'participation',
            'projet',
            'commentaires',
        ]
        widgets = {
            'inscription': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'examen_mi_parcours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': 'Sur 100',
            }),
            'examen_final': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': 'Sur 100',
            }),
            'travaux': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': 'Sur 100',
            }),
            'participation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': 'Sur 100',
            }),
            'projet': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': 'Sur 100',
            }),
            'commentaires': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Commentaires optionnels...',
            }),
        }
        labels = {
            'inscription':         'Inscription (Étudiant – Cours)',
            'examen_mi_parcours':  'Examen mi-parcours (25 %)',
            'examen_final':        'Examen final (35 %)',
            'travaux':             'Travaux pratiques (20 %)',
            'participation':       'Participation (10 %)',
            'projet':              'Projet (10 %)',
            'commentaires':        'Commentaires',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            # Mode création : uniquement les inscriptions actives sans note
            self.fields['inscription'].queryset = Inscription.objects.filter(
                statut='INSCRIT',           # ← corrigé (était status='ENROLLED')
                note__isnull=True,
            ).select_related(
                'etudiant__utilisateur',    # ← corrigé (était student__user)
                'section_cours__cours',     # ← corrigé (était course_section__course)
            ).order_by('etudiant__numero_etudiant')   # ← corrigé
        else:
            # Mode modification : inscription non modifiable
            self.fields['inscription'].disabled = True

        # Libellé personnalisé pour chaque inscription
        self.fields['inscription'].label_from_instance = lambda obj: (
            f"{obj.etudiant.numero_etudiant} - "
            f"{obj.etudiant.utilisateur.get_full_name()} | "
            f"{obj.section_cours.cours.code} - "
            f"Section {obj.section_cours.numero_section}"
        )

    def clean(self):
        donnees = super().clean()

        composantes = [
            donnees.get('examen_mi_parcours'),
            donnees.get('examen_final'),
            donnees.get('travaux'),
            donnees.get('participation'),
            donnees.get('projet'),
        ]

        if not any(composantes):
            raise forms.ValidationError(
                'Veuillez renseigner au moins une composante de la note.'
            )

        return donnees


class FormulaireFiltrageNotes(forms.Form):
    """Formulaire de filtrage de la liste des notes"""

    matricule = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Matricule ou nom...',
        }),
        label='Étudiant',
    )

    code_cours = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : PSY101',
        }),
        label='Code cours',
    )

    mention = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes')] + [
            ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('F', 'F'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mention',
    )

    etat = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous'),
            ('complete', 'Complètes'),
            ('incomplete', 'Incomplètes'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='État',
    )

    note_min = forms.DecimalField(
        required=False, min_value=0, max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        label='Note min',
    )

    note_max = forms.DecimalField(
        required=False, min_value=0, max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '100'}),
        label='Note max',
    )