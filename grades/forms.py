from django import forms
from .models import Grade
from enrollments.models import Enrollment


# ========== grades/forms.py ==========


class GradeForm(forms.ModelForm):
    """Formulaire unique pour la gestion des notes (création et modification)"""
    
    class Meta:
        model = Grade
        fields = [
            'enrollment',
            'midterm_exam',
            'final_exam',
            'assignments',
            'participation',
            'project',
            'comments'
        ]
        widgets = {
            'enrollment': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'midterm_exam': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Sur 100'
            }),
            'final_exam': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Sur 100'
            }),
            'assignments': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Sur 100'
            }),
            'participation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Sur 100'
            }),
            'project': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Sur 100'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Commentaires optionnels...'
            }),
        }
        labels = {
            'enrollment': 'Inscription (Étudiant - Cours)',
            'midterm_exam': 'Examen mi-parcours (25%)',
            'final_exam': 'Examen final (35%)',
            'assignments': 'Travaux pratiques (20%)',
            'participation': 'Participation (10%)',
            'project': 'Projet (10%)',
            'comments': 'Commentaires',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # MODE CRÉATION : Filtrer pour n'afficher que les inscriptions actives sans note
        if not self.instance.pk:
            self.fields['enrollment'].queryset = Enrollment.objects.filter(
                status='ENROLLED',
                grade__isnull=True
            ).select_related(
                'student__user',
                'course_section__course'
            ).order_by('student__student_number')
        else:
            # MODE MODIFICATION : Désactiver le champ enrollment (non modifiable)
            self.fields['enrollment'].disabled = True
        
        # Personnaliser l'affichage des enrollments
        self.fields['enrollment'].label_from_instance = lambda obj: (
            f"{obj.student.student_number} - "
            f"{obj.student.user.get_full_name()} | "
            f"{obj.course_section.course.code} - "
            f"Section {obj.course_section.section_number}"
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier qu'au moins une composante est remplie
        components = [
            cleaned_data.get('midterm_exam'),
            cleaned_data.get('final_exam'),
            cleaned_data.get('assignments'),
            cleaned_data.get('participation'),
            cleaned_data.get('project'),
        ]
        
        if not any(components):
            raise forms.ValidationError(
                'Veuillez renseigner au moins une composante de la note.'
            )
        
        return cleaned_data

class GradeFilterForm(forms.Form):
    """Formulaire de filtrage des notes"""
    
    student_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Matricule ou nom...'
        }),
        label='Étudiant'
    )
    
    course_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: PSY101'
        }),
        label='Code cours'
    )
    
    letter_grade = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes')] + [
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
            ('F', 'F'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mention'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous'),
            ('complete', 'Complètes'),
            ('incomplete', 'Incomplètes'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='État'
    )
    
    min_grade = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label='Note min'
    )
    
    max_grade = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '100'
        }),
        label='Note max'
    )



