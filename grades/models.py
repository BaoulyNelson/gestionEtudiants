from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Grade(models.Model):
    """Modèle pour les notes des étudiants"""
    
    enrollment = models.OneToOneField(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='grade',
        verbose_name='Inscription'
    )
    
    # Différentes composantes de la note
    midterm_exam = models.DecimalField(
        'Examen de mi-parcours',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    final_exam = models.DecimalField(
        'Examen final',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    assignments = models.DecimalField(
        'Travaux/Devoirs',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    participation = models.DecimalField(
        'Participation',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    project = models.DecimalField(
        'Projet',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    # Note finale calculée
    final_grade = models.DecimalField(
        'Note finale',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    letter_grade = models.CharField('Note lettre', max_length=2, blank=True)
    
    # Commentaires du professeur
    comments = models.TextField('Commentaires', blank=True)
    
    # Suivi
    graded_by = models.ForeignKey(
        'accounts.Professor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='graded_students',
        verbose_name='Noté par'
    )
    
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Date de modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['-updated_at']
    
    def __str__(self):
        return (f"{self.enrollment.student.student_number} - "
                f"{self.enrollment.course_section.course.code} - "
                f"{self.final_grade or 'Non noté'}")
    
    def calculate_final_grade(self):
        """Calcule la note finale selon les pondérations"""
        weights = {
            'midterm_exam': 0.25,      # 25%
            'final_exam': 0.35,        # 35%
            'assignments': 0.20,       # 20%
            'participation': 0.10,     # 10%
            'project': 0.10,           # 10%
        }
        
        total = 0
        total_weight = 0
        
        for component, weight in weights.items():
            value = getattr(self, component)
            if value is not None:
                total += float(value) * weight
                total_weight += weight
        
        if total_weight > 0:
            self.final_grade = round(total / total_weight, 2)
        else:
            self.final_grade = None
        
        # Calculer la note lettre
        if self.final_grade is not None:
            self.letter_grade = self.get_letter_grade(float(self.final_grade))
        
        return self.final_grade
    
    @staticmethod
    def get_letter_grade(grade):
        """Convertit une note numérique en note lettre"""
        if grade >= 90:
            return 'A'
        elif grade >= 80:
            return 'B'
        elif grade >= 70:
            return 'C'
        elif grade >= 60:
            return 'D'
        else:
            return 'F'
    
    def save(self, *args, **kwargs):
        """Recalculer la note finale avant de sauvegarder"""
        self.calculate_final_grade()
        super().save(*args, **kwargs)
    
    def is_passing(self):
        """Vérifie si l'étudiant a réussi le cours"""
        if self.final_grade is None:
            return None
        return float(self.final_grade) >= 60


class GradeHistory(models.Model):
    """Historique des modifications de notes"""
    
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Note'
    )
    
    component = models.CharField('Composante', max_length=50)
    old_value = models.DecimalField(
        'Ancienne valeur',
        max_digits=5,
        decimal_places=2,
        null=True
    )
    new_value = models.DecimalField(
        'Nouvelle valeur',
        max_digits=5,
        decimal_places=2,
        null=True
    )
    
    modified_by = models.ForeignKey(
        'accounts.Professor',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modifié par'
    )
    
    modified_at = models.DateTimeField('Date de modification', auto_now_add=True)
    reason = models.TextField('Raison', blank=True)
    
    class Meta:
        verbose_name = 'Historique de note'
        verbose_name_plural = 'Historiques de notes'
        ordering = ['-modified_at']
    
    def __str__(self):
        return (f"{self.grade.enrollment.student.student_number} - "
                f"{self.component}: {self.old_value} → {self.new_value}")


class Transcript(models.Model):
    """Relevé de notes complet d'un étudiant"""
    
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='transcripts',
        verbose_name='Étudiant'
    )
    
    semester = models.CharField('Semestre', max_length=20)
    year = models.IntegerField('Année académique')
    
    # Statistiques
    gpa = models.DecimalField(
        'Moyenne générale (GPA)',
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        null=True,
        blank=True
    )
    
    total_credits_attempted = models.IntegerField('Crédits tentés', default=0)
    total_credits_earned = models.IntegerField('Crédits obtenus', default=0)
    
    generated_at = models.DateTimeField('Date de génération', auto_now=True)
    
    class Meta:
        verbose_name = 'Relevé de notes'
        verbose_name_plural = 'Relevés de notes'
        ordering = ['-year', '-semester']
        unique_together = ['student', 'semester', 'year']
    
    def __str__(self):
        return (f"{self.student.student_number} - "
                f"{self.semester} {self.year}")
    
    def calculate_gpa(self):
        """Calcule le GPA pour ce semestre"""
        enrollments = self.student.enrollments.filter(
            course_section__semester=self.semester,
            course_section__year=self.year,
            status='COMPLETED'
        )
        
        total_points = 0
        total_credits = 0
        
        for enrollment in enrollments:
            try:
                grade = enrollment.grade
                if grade.final_grade is not None:
                    # Convertir la note en points GPA (échelle 4.0)
                    grade_value = float(grade.final_grade)
                    if grade_value >= 90:
                        points = 4.0
                    elif grade_value >= 80:
                        points = 3.0
                    elif grade_value >= 70:
                        points = 2.0
                    elif grade_value >= 60:
                        points = 1.0
                    else:
                        points = 0.0
                    
                    credits = enrollment.course_section.course.credits
                    total_points += points * credits
                    total_credits += credits
                    
                    if grade.is_passing():
                        self.total_credits_earned += credits
            except Grade.DoesNotExist:
                pass
        
        self.total_credits_attempted = total_credits
        
        if total_credits > 0:
            self.gpa = round(total_points / total_credits, 2)
        else:
            self.gpa = None
        
        return self.gpa