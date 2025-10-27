from django import forms
from .models import Course, CourseSection, Prerequisite


class CourseForm(forms.ModelForm):
    """Formulaire de création/modification de cours"""
    class Meta:
        model = Course
        fields = [
            'code', 'name', 'description', 'credits',
            'department', 'year_level', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'year_level': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseSectionForm(forms.ModelForm):
    """Formulaire de création/modification de section de cours"""
    class Meta:
        model = CourseSection
        fields = [
            'course', 'section_number', 'professor',
            'day_of_week', 'start_time', 'end_time', 'room',
            'session', 'semester', 'year',
            'max_students', 'is_open'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'section_number': forms.TextInput(attrs={'class': 'form-control'}),
            'professor': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PrerequisiteForm(forms.ModelForm):
    """Formulaire pour ajouter des prérequis"""
    class Meta:
        model = Prerequisite
        fields = ['course', 'prerequisite_course']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'prerequisite_course': forms.Select(attrs={'class': 'form-select'}),
        }