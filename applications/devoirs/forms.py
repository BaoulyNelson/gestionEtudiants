from django import forms
from django.core.exceptions import ValidationError

from .models import Devoir, FichierDevoir, Remise, FichierRemise


# ─── Extensions autorisées ────────────────────────────────────────────────────
EXTENSIONS_DEVOIR  = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
                       'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'txt']
EXTENSIONS_REMISE  = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
                       'zip', 'jpg', 'jpeg', 'png', 'txt']
TAILLE_MAX_OCTETS  = 20 * 1024 * 1024   # 20 Mo par fichier


# ─── Widget multi-fichiers ────────────────────────────────────────────────────

class MultipleFileInput(forms.FileInput):
    """FileInput qui autorise la sélection de plusieurs fichiers à la fois."""
    allow_multiple_selected = True


# ─── Fonctions de validation ──────────────────────────────────────────────────

def valider_extension(fichier, extensions_ok):
    ext = fichier.name.rsplit('.', 1)[-1].lower() if '.' in fichier.name else ''
    if ext not in extensions_ok:
        raise ValidationError(
            f"Extension « .{ext} » non autorisée. "
            f"Formats acceptés : {', '.join(extensions_ok)}."
        )


def valider_taille(fichier, taille_max=TAILLE_MAX_OCTETS):
    if fichier.size > taille_max:
        raise ValidationError(
            f"Le fichier dépasse la taille maximale autorisée "
            f"({taille_max // (1024*1024)} Mo)."
        )


# ─── Formulaire principal du devoir ──────────────────────────────────────────

class FormulaireDevoir(forms.ModelForm):
    class Meta:
        model  = Devoir
        fields = [
            'titre', 'description', 'consignes',
            'type_devoir', 'date_publication', 'date_limite',
            'points_max', 'est_publie',
        ]
        widgets = {
            'titre':       forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex. : Rapport de stage — Chapitre 1',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Résumé affiché dans la liste des devoirs',
            }),
            'consignes':   forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': 'Instructions détaillées, critères d\'évaluation…',
            }),
            'type_devoir': forms.Select(attrs={'class': 'form-select'}),
            'date_publication': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'date_limite': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'points_max':  forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'est_publie':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titre':            'Titre du devoir',
            'description':      'Description courte',
            'consignes':        'Consignes détaillées',
            'type_devoir':      'Type de travail attendu',
            'date_publication': 'Date de publication (optionnel)',
            'date_limite':      'Date limite de remise',
            'points_max':       'Barème (points max)',
            'est_publie':       'Publier et rendre visible aux étudiants',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formater les champs date pour l'input datetime-local
        for champ in ('date_publication', 'date_limite'):
            valeur = getattr(self.instance, champ, None)
            if valeur:
                self.initial[champ] = valeur.strftime('%Y-%m-%dT%H:%M')
        self.fields['date_publication'].required = False
        self.fields['consignes'].required        = False

    def clean(self):
        cleaned = super().clean()
        pub   = cleaned.get('date_publication')
        limit = cleaned.get('date_limite')
        if pub and limit and pub >= limit:
            raise ValidationError(
                "La date de publication doit être antérieure à la date limite de remise."
            )
        return cleaned


# ─── Formulaire d'ajout d'un fichier joint (devoir) ──────────────────────────

class FormulaireFichierDevoir(forms.ModelForm):
    class Meta:
        model  = FichierDevoir
        fields = ['fichier', 'nom']
        widgets = {
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'nom':     forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom affiché aux étudiants',
            }),
        }
        labels = {
            'fichier': 'Fichier à joindre',
            'nom':     'Nom du fichier',
        }

    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        if fichier:
            valider_extension(fichier, EXTENSIONS_DEVOIR)
            valider_taille(fichier)
        return fichier


# ─── Formulaire multi-fichiers pour le devoir ────────────────────────────────

class FormulaireMultiFichiersDevoir(forms.Form):
    """Utilisé dans la vue de création/modification via formset ou en standalone."""
    fichiers = forms.FileField(
        label='Fichiers joints',
        widget=MultipleFileInput(attrs={
            'class':  'form-control',
            'accept': ','.join(f'.{e}' for e in EXTENSIONS_DEVOIR),
        }),
        required=False,
        help_text=f"Formats : {', '.join(EXTENSIONS_DEVOIR)} | Max 20 Mo par fichier",
    )

    def clean_fichiers(self):
        fichiers = self.files.getlist('fichiers')
        for f in fichiers:
            valider_extension(f, EXTENSIONS_DEVOIR)
            valider_taille(f)
        return fichiers


# ─── Formulaire de remise (étudiant) ─────────────────────────────────────────

class FormulaireRemise(forms.ModelForm):
    """
    Adapte les champs selon le type du devoir.
    Passe `type_devoir=` au constructeur.
    """
    class Meta:
        model  = Remise
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 10,
                'placeholder': 'Rédigez votre réponse ici…',
            }),
        }
        labels = {'contenu': 'Votre réponse'}

    def __init__(self, *args, type_devoir=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_devoir = type_devoir
        if type_devoir in ('FICHIER', 'QCM'):
            self.fields['contenu'].required = False
            self.fields['contenu'].widget   = forms.HiddenInput()


class FormulaireFichiersRemise(forms.Form):
    """Gestion des fichiers soumis par l'étudiant (multi-fichiers)."""
    fichiers = forms.FileField(
        label='Fichier(s) à soumettre',
        widget=MultipleFileInput(attrs={
            'class':  'form-control',
            'accept': ','.join(f'.{e}' for e in EXTENSIONS_REMISE),
        }),
        required=False,
        help_text=f"Formats acceptés : {', '.join(EXTENSIONS_REMISE)} | Max 20 Mo par fichier",
    )

    def clean_fichiers(self):
        fichiers = self.files.getlist('fichiers')
        for f in fichiers:
            valider_extension(f, EXTENSIONS_REMISE)
            valider_taille(f)
        return fichiers


# ─── Formulaire de notation ───────────────────────────────────────────────────

class FormulaireNote(forms.ModelForm):
    class Meta:
        model  = Remise
        fields = ['note', 'commentaire_prof']
        widgets = {
            'note': forms.NumberInput(attrs={
                'class': 'form-control',
                'step':  '0.5',
                'min':   '0',
            }),
            'commentaire_prof': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        5,
                'placeholder': 'Retour personnalisé à l\'étudiant…',
            }),
        }
        labels = {
            'note':             'Note attribuée',
            'commentaire_prof': 'Commentaire / Rétroaction',
        }

    def __init__(self, *args, points_max=None, **kwargs):
        super().__init__(*args, **kwargs)
        if points_max:
            self.fields['note'].widget.attrs['max'] = points_max
            self.fields['note'].label = f"Note (sur {points_max})"
        self.fields['commentaire_prof'].required = False

    def clean_note(self):
        note       = self.cleaned_data.get('note')
        points_max = self.instance.devoir.points_max if self.instance and self.instance.pk else None
        if note is not None and points_max is not None and note > points_max:
            raise ValidationError(
                f"La note ne peut pas dépasser le barème ({points_max} points)."
            )
        if note is not None and note < 0:
            raise ValidationError("La note ne peut pas être négative.")
        return note