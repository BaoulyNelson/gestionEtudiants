

from datetime import timezone
from django.db import models
from django.utils import timezone
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = (
        ('note_publiee', 'Note publiée'),
        ('note_modifiee', 'Note modifiée'),
        ('inscription_confirmee', 'Inscription confirmée'),
    )

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=30, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    est_lue = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(null=True, blank=True)
    lien = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-date_creation']

    def __str__(self):
        return f"Notification - {self.titre}"

    def marquer_comme_lue(self):
        if not self.est_lue:
            self.est_lue = True
            self.date_lecture = timezone.now()
            self.save()