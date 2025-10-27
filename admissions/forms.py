from django import forms
from .models import Candidature

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['prenom', 'nom', 'email', 'telephone', 'programme', 'lettre_motivation', 'accepte_conditions']
        widgets = {
            'prenom': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre prénom',
                'id': 'firstName'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Votre nom de famille',
                'id': 'lastName'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'votre.email@exemple.com',
                'id': 'email'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+509 XXXX-XXXX',
                'id': 'phone'
            }),
            'programme': forms.Select(attrs={
                'class': 'form-input',
                'id': 'program'
            }),
            'lettre_motivation': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Expliquez pourquoi vous souhaitez étudier à FASCH...',
                'rows': 4,
                'id': 'motivation'
            }),
            'accepte_conditions': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary-200',
                'id': 'terms'
            }),
        }
    
    def clean_accepte_conditions(self):
        accepte = self.cleaned_data.get('accepte_conditions')
        if not accepte:
            raise forms.ValidationError("Vous devez accepter les conditions d'admission.")
        return accepte

