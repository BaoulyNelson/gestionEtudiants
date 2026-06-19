from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Professeur, Etudiant, Administrateur


@receiver(post_save, sender=get_user_model())
def creer_ou_mettre_a_jour_profil(sender, instance, created, **kwargs):
    """Crée le profil lié automatiquement selon le rôle."""

    if instance.role == 'PROFESSEUR':
        Professeur.objects.get_or_create(
            utilisateur=instance,
            defaults={
                'identifiant_professeur': f"PROF{instance.id:04d}",
                'date_embauche': timezone.now().date(),
                'departement': None,
                'specialite': ''
            }
        )
        if hasattr(instance, 'profil_etudiant'):
            instance.profil_etudiant.delete()
        if hasattr(instance, 'profil_admin'):
            instance.profil_admin.delete()

    elif instance.role == 'ETUDIANT':
        Etudiant.objects.get_or_create(
            utilisateur=instance,
            defaults={
                'numero_etudiant': f"ETU{instance.id:04d}",
                'departement': None,
                'niveau': 'PREPARATOIRE',
                'date_inscription': timezone.now().date()
            }
        )
        if hasattr(instance, 'profil_professeur'):
            instance.profil_professeur.delete()
        if hasattr(instance, 'profil_admin'):
            instance.profil_admin.delete()

    elif instance.role in ('ADMIN', 'SUPERUTILISATEUR'):
        Administrateur.objects.get_or_create(
            utilisateur=instance,
            defaults={
                'identifiant_administrateur': f"ADM{instance.id:04d}",
                'poste': 'Administrateur'
            }
        )
        if hasattr(instance, 'profil_etudiant'):
            instance.profil_etudiant.delete()
        if hasattr(instance, 'profil_professeur'):
            instance.profil_professeur.delete()