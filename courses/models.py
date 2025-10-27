from django.db import models
from django.core.exceptions import ValidationError
from datetime import time

class Course(models.Model):
    """Modèle pour les cours"""
    
    YEAR_CHOICES = [
        (1, 'Année Préparatoire'),
        (2, 'Deuxième Année'),
        (3, 'Troisième Année'),
        (4, 'Quatrième Année'),
    ]
    
    code = models.CharField('Code du cours', max_length=20, unique=True)
    name = models.CharField('Nom du cours', max_length=200)
    description = models.TextField('Description', blank=True)
    credits = models.IntegerField('Crédits')
    
    department = models.ForeignKey('departments.Department',on_delete=models.CASCADE,related_name='courses',verbose_name='Département', null=True, blank=True) 
    year_level = models.IntegerField('Année d\'études', choices=YEAR_CHOICES)
    
    # Statut du cours
    is_active = models.BooleanField('Actif', default=True)
    
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Date de modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseSection(models.Model):
    """Section de cours avec horaire et professeur spécifique"""
    
    DAYS_CHOICES = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
    ]
    
    SESSION_CHOICES = [
        ('SESSION_1', 'Session 1'),
        ('SESSION_2', 'Session 2'),
    ]
    
    SEMESTER_CHOICES = [
        ('FALL', 'Automne'),
        ('SPRING', 'Printemps'),
        ('SUMMER', 'Été'),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Cours'
    )
    
    section_number = models.CharField('Numéro de section', max_length=10)
    
    professor = models.ForeignKey(
        'accounts.Professor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='course_sections',
        verbose_name='Professeur'
    )
    
    # Horaire
    day_of_week = models.CharField('Jour', max_length=20, choices=DAYS_CHOICES)
    start_time = models.TimeField('Heure de début')
    end_time = models.TimeField('Heure de fin')
    room = models.CharField('Salle', max_length=50, blank=True)
    
    # Session et semestre
    session = models.CharField('Session', max_length=20, choices=SESSION_CHOICES)
    semester = models.CharField('Semestre', max_length=20, choices=SEMESTER_CHOICES)
    year = models.IntegerField('Année académique')
    
    # Capacité
    max_students = models.IntegerField('Nombre maximum d\'étudiants', default=30)
    is_open = models.BooleanField('Ouvert aux inscriptions', default=True)
    
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Date de modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Section de cours'
        verbose_name_plural = 'Sections de cours'
        ordering = ['course__code', 'section_number']
        unique_together = ['course', 'section_number', 'session', 'semester', 'year']
    
    def __str__(self):
        return f"{self.course.code}-{self.section_number} ({self.get_session_display()})"
    
    def clean(self):
        """Validation des horaires"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(
                    'L\'heure de début doit être avant l\'heure de fin.'
                )
    
    def get_enrolled_count(self):
        """Retourne le nombre d'étudiants inscrits"""
        return self.enrollments.filter(status='ENROLLED').count()
    
    def is_full(self):
        """Vérifie si la section est pleine"""
        return self.get_enrolled_count() >= self.max_students
    
    def can_enroll(self):
        """Vérifie si on peut s'inscrire à cette section"""
        return self.is_open and not self.is_full()
    
    def has_schedule_conflict(self, day, start_time, end_time):
        """Vérifie s'il y a conflit d'horaire"""
        if self.day_of_week != day:
            return False
        
        # Vérifier le chevauchement des horaires
        return not (end_time <= self.start_time or start_time >= self.end_time)


class Prerequisite(models.Model):
    """Prérequis pour les cours"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='prerequisites',
        verbose_name='Cours'
    )
    
    prerequisite_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='required_for',
        verbose_name='Cours prérequis'
    )
    
    class Meta:
        verbose_name = 'Prérequis'
        verbose_name_plural = 'Prérequis'
        unique_together = ['course', 'prerequisite_course']
    
    def __str__(self):
        return f"{self.course.code} nécessite {self.prerequisite_course.code}"
    
    def clean(self):
        """Validation pour éviter les prérequis circulaires"""
        if self.course == self.prerequisite_course:
            raise ValidationError(
                'Un cours ne peut pas être son propre prérequis.'
            )