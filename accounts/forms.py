from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Student, Professor, Admin


class LoginForm(forms.Form):
    """Formulaire de connexion"""
    username = forms.CharField(
        label='Email ou téléphone',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'tonexemple@gmail.com ou +50912345678',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'motdepasse123'
        })
    )




class ChangePasswordForm(PasswordChangeForm):
    """Formulaire de changement de mot de passe"""
    old_password = forms.CharField(
        label='Ancien mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ancien mot de passe'
        })
    )
    new_password1 = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        }),
        help_text='Minimum 8 caractères'
    )
    new_password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    )


class UserCreationForm(forms.ModelForm):
    """Formulaire de création d'utilisateur"""
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'role',
            'phone_number', 'address', 'date_of_birth',
            'profile_picture', 'is_active'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserUpdateForm(forms.ModelForm):
    """Formulaire de modification d'utilisateur"""
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name',
            'phone_number', 'address', 'date_of_birth',
            'profile_picture', 'is_active'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StudentCreationForm(forms.ModelForm):
    """Formulaire de création de profil étudiant"""
    class Meta:
        model = Student
        fields = ['student_number', 'department', 'current_year', 'enrollment_date']
        widgets = {
            'student_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'current_year': forms.Select(attrs={'class': 'form-select'}),
            'enrollment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class StudentUpdateForm(forms.ModelForm):
    """Formulaire de modification de profil étudiant"""
    class Meta:
        model = Student
        fields = ['department', 'current_year']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'current_year': forms.Select(attrs={'class': 'form-select'}),
        }


class ProfessorCreationForm(forms.ModelForm):
    """Formulaire de création de profil professeur"""
    class Meta:
        model = Professor
        fields = ['professor_id', 'department', 'specialization', 'hire_date']
        widgets = {
            'professor_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class ProfessorUpdateForm(forms.ModelForm):
    """Formulaire de modification de profil professeur"""
    class Meta:
        model = Professor
        fields = ['department', 'specialization']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AdminCreationForm(forms.ModelForm):
    """Formulaire de création de profil administrateur"""
    class Meta:
        model = Admin
        fields = ['admin_id', 'position']
        widgets = {
            'admin_id': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
        

class UserProfileForm(UserUpdateForm):
    """Formulaire simplifié pour la page de profil personnelle"""
    class Meta(UserUpdateForm.Meta):
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'address',
            'date_of_birth',
            'profile_picture',
        ]
