from django.db import models

class Department(models.Model):
    """Modèle pour les départements de FASCH"""
    
    DEPARTMENT_CHOICES = [
        ('PSYCHO', 'Psychologie'),
        ('COMM', 'Communication sociale'),
        ('SOCIO', 'Sociologie'),
        ('SERVSOC', 'Service social'),
    ]
    
    code = models.CharField(
        'Code', 
        max_length=20, 
        unique=True, 
        choices=DEPARTMENT_CHOICES
    )
    name = models.CharField('Nom du département', max_length=100, unique=True)
    description = models.TextField('Description', blank=True)
    head_of_department = models.ForeignKey(
        'accounts.Professor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department',
        verbose_name='Chef de département'
    )
    
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Date de modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_total_students(self):
        """Retourne le nombre total d'étudiants dans le département"""
        return self.students.filter(user__is_active=True).count()
    
    def get_total_professors(self):
        """Retourne le nombre total de professeurs dans le département"""
        return self.professors.filter(user__is_active=True).count()