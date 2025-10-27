# ========== notifications/signals.py (CORRIGÉ) ==========
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from grades.models import Grade
from notifications.utils import _envoyer_notification_note

@receiver(pre_save, sender=Grade)
def sauvegarder_ancienne_note(sender, instance, **kwargs):
    """
    Sauvegarder toutes les composantes de la note avant modification.
    """
    if instance.pk:
        try:
            ancienne = Grade.objects.get(pk=instance.pk)
            instance._ancienne_valeurs = {
                'midterm_exam': ancienne.midterm_exam,
                'final_exam': ancienne.final_exam,
                'assignments': ancienne.assignments,
                'participation': ancienne.participation,
                'project': ancienne.project,
                'final_grade': ancienne.final_grade,
                'letter_grade': ancienne.letter_grade,
            }
        except Grade.DoesNotExist:
            instance._ancienne_valeurs = None
    else:
        instance._ancienne_valeurs = None


@receiver(post_save, sender=Grade)
def notifier_etudiant_note(sender, instance, created, **kwargs):
    """
    Notifier l'étudiant si une note a été créée ou modifiée.
    """
    anciennes = getattr(instance, '_ancienne_valeurs', None)

    # Vérifier si la note est publiée (ou considérée publiée par défaut)
    if getattr(instance, 'is_published', True):
        changements = None

        if anciennes:
            # Comparer chaque champ et ne garder que ceux qui ont changé
            changements = {}
            for champ, ancienne_valeur in anciennes.items():
                nouvelle_valeur = getattr(instance, champ)
                if ancienne_valeur != nouvelle_valeur:
                    changements[champ] = {
                        'ancienne': ancienne_valeur,
                        'nouvelle': nouvelle_valeur
                    }

        # ⚠️ CORRECTION : Utiliser anciennes_valeurs= au lieu de changements=
        _envoyer_notification_note(
            etudiant=instance.enrollment.student,
            note=instance,
            anciennes_valeurs=changements  # ✅ Nom correct du paramètre
        )






