# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from .models import Professor, Student, Admin

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_related_profile(sender, instance, created, **kwargs):
    """
    Crée le profil lié automatiquement selon le rôle.
    Fonctionne à la création et lors d'un changement de rôle.
    """
    
    # PROFESSEUR
    if instance.role == 'PROFESSOR':
        professor, _ = Professor.objects.get_or_create(
            user=instance,
            defaults={
                'professor_id': f"PROF{instance.id:04d}",
                'hire_date': timezone.now().date(),
                'department': None,
                'specialization': ''
            }
        )
        # Supprimer les autres profils si existants
        if hasattr(instance, 'student_profile'):
            instance.student_profile.delete()
        if hasattr(instance, 'admin_profile'):
            instance.admin_profile.delete()
    
    # ÉTUDIANT
    elif instance.role == 'STUDENT':
        student, _ = Student.objects.get_or_create(
            user=instance,
            defaults={
                'student_number': f"STU{instance.id:04d}",
                'department': None,
                'current_year': 1,
                'enrollment_date': timezone.now().date()
            }
        )
        if hasattr(instance, 'professor_profile'):
            instance.professor_profile.delete()
        if hasattr(instance, 'admin_profile'):
            instance.admin_profile.delete()
    
    # ADMIN
    elif instance.role == 'ADMIN':
        admin, _ = Admin.objects.get_or_create(
            user=instance,
            defaults={
                'admin_id': f"ADM{instance.id:04d}",
                'position': 'Administrateur'
            }
        )
        if hasattr(instance, 'student_profile'):
            instance.student_profile.delete()
        if hasattr(instance, 'professor_profile'):
            instance.professor_profile.delete()
