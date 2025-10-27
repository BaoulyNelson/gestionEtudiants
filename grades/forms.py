from django import forms
from .models import Grade


class GradeForm(forms.ModelForm):
    """Formulaire de saisie de notes"""
    class Meta:
        model = Grade
        fields = [
            'midterm_exam', 'final_exam', 'assignments',
            'participation', 'project', 'comments'
        ]
        widgets = {
            'midterm_exam': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'final_exam': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'assignments': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'participation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'project': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
        labels = {
            'midterm_exam': 'Examen de mi-parcours (25%)',
            'final_exam': 'Examen final (35%)',
            'assignments': 'Travaux/Devoirs (20%)',
            'participation': 'Participation (10%)',
            'project': 'Projet (10%)',
            'comments': 'Commentaires',
        }