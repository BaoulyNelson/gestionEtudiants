from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from applications.notes.models import Note
from applications.notifications.utils import _envoyer_notification_note


@receiver(pre_save, sender=Note)
def sauvegarder_ancienne_note(sender, instance, **kwargs):
    """
    Sauvegarde les anciennes valeurs avant modification.
    """

    if instance.pk:
        try:
            ancienne = Note.objects.get(pk=instance.pk)

            instance._ancienne_valeurs = {
                'examen_mi_parcours': ancienne.examen_mi_parcours,
                'examen_final': ancienne.examen_final,
                'travaux': ancienne.travaux,
                'participation': ancienne.participation,
                'projet': ancienne.projet,
                'note_finale': ancienne.note_finale,
                'mention': ancienne.mention,
            }

        except Note.DoesNotExist:
            instance._ancienne_valeurs = None
    else:
        instance._ancienne_valeurs = None


@receiver(post_save, sender=Note)
def notifier_etudiant_note(sender, instance, created, **kwargs):
    """
    Envoie une notification après création ou modification d'une note.
    """

    anciennes = getattr(instance, '_ancienne_valeurs', None)

    # Construire dictionnaire des changements
    changements = {}

    if anciennes:
        for champ, ancienne_valeur in anciennes.items():
            nouvelle_valeur = getattr(instance, champ)

            if ancienne_valeur != nouvelle_valeur:
                changements[champ] = {
                    'ancienne': ancienne_valeur,
                    'nouvelle': nouvelle_valeur
                }

    # Appel propre du service
    _envoyer_notification_note(
        etudiant=instance.inscription.etudiant,
        note=instance,
        anciennes_valeurs=changements if changements else None
    )