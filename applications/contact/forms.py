from django import forms
from .models import MessageContact

_INPUT = 'form-control'


class FormulaireContact(forms.ModelForm):
    class Meta:
        model  = MessageContact
        fields = ['nom', 'email', 'sujet', 'message']
        widgets = {
            'nom':     forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Votre nom complet'}),
            'email':   forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'votre@email.com'}),
            'sujet':   forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': _INPUT, 'rows': 6,
                       'placeholder': 'Redigez votre message...', 'maxlength': '3000'}),
        }
        labels = {
            'nom': 'Nom complet *', 'email': 'Adresse email *',
            'sujet': 'Sujet *',     'message': 'Message *',
        }
