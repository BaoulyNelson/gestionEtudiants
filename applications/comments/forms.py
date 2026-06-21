from django import forms
from .models import Commentaire


class FormulaireCommentaire(forms.ModelForm):
    class Meta:
        model  = Commentaire
        fields = ['contenu', 'parent']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': 'Redigez votre commentaire...',
                'maxlength':   '2000',
            }),
            'parent': forms.HiddenInput(),
        }
        labels = {'contenu': 'Votre commentaire'}
