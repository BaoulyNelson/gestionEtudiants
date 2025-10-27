from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

class Enrollment(models.Model):
    """Modèle pour les inscriptions des étudiants aux sections de cours"""
    
    STATUS_CHOICES = [
        ('ENROLLED', 'Inscrit'),
        ('DROPPED', 'Abandonné'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
    ]
    
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Étudiant'
    )
    
    course_section = models.ForeignKey(
        'courses.CourseSection',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Section de cours'
    )
    
    status = models.CharField(
        'Statut', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ENROLLED'
    )
    
    enrollment_date = models.DateTimeField('Date d\'inscription', auto_now_add=True)
    drop_date = models.DateTimeField('Date d\'abandon', null=True, blank=True)
    
    # Notes (sera lié au modèle Grade)
    
    class Meta:
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering = ['-enrollment_date']
        unique_together = ['student', 'course_section']
    
    def __str__(self):
        return (f"{self.student.student_number} - "
                f"{self.course_section.course.code}-"
                f"{self.course_section.section_number}")
    
    def clean(self):
        """Validation des inscriptions"""
        if not self.pk:  # Nouvelle inscription
            # Vérifier le nombre maximum de cours par session
            session_enrollments = Enrollment.objects.filter(
                student=self.student,
                course_section__session=self.course_section.session,
                course_section__semester=self.course_section.semester,
                course_section__year=self.course_section.year,
                status='ENROLLED'
            ).count()
            
            max_courses = getattr(settings, 'MAX_COURSES_PER_SESSION', 8)
            if session_enrollments >= max_courses:
                raise ValidationError(
                    f'L\'étudiant a déjà atteint le maximum de '
                    f'{max_courses} cours pour cette session.'
                )
            
            # Vérifier si la section est ouverte et pas pleine
            if not self.course_section.can_enroll():
                raise ValidationError(
                    'Cette section n\'est pas disponible pour inscription.'
                )
            
            # Vérifier les conflits d'horaire
            conflicting_enrollments = Enrollment.objects.filter(
                student=self.student,
                course_section__session=self.course_section.session,
                course_section__semester=self.course_section.semester,
                course_section__year=self.course_section.year,
                course_section__day_of_week=self.course_section.day_of_week,
                status='ENROLLED'
            )
            
            for enrollment in conflicting_enrollments:
                section = enrollment.course_section
                if section.has_schedule_conflict(
                    self.course_section.day_of_week,
                    self.course_section.start_time,
                    self.course_section.end_time
                ):
                    raise ValidationError(
                        f'Conflit d\'horaire avec le cours '
                        f'{section.course.code}-{section.section_number}.'
                    )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EnrollmentHistory(models.Model):
    """Historique des modifications d'inscription"""
    
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Inscription'
    )
    
    previous_status = models.CharField('Statut précédent', max_length=20)
    new_status = models.CharField('Nouveau statut', max_length=20)
    changed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modifié par'
    )
    changed_at = models.DateTimeField('Date de modification', auto_now_add=True)
    reason = models.TextField('Raison', blank=True)
    
    class Meta:
        verbose_name = 'Historique d\'inscription'
        verbose_name_plural = 'Historiques d\'inscription'
        ordering = ['-changed_at']
    
    def __str__(self):
        return (f"{self.enrollment.student.student_number} - "
                f"{self.previous_status} → {self.new_status}")