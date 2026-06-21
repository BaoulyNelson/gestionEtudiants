from django.db import models


class MessageContact(models.Model):
    SUJET_CHOICES = [
        ('general',      'Demande generale'),
        ('redaction',    'Contacter la redaction'),
        ('correction',   'Signaler une erreur'),
        ('partenariat',  'Proposition de partenariat'),
        ('publicite',    'Publicite'),
        ('technique',    'Probleme technique'),
        ('autre',        'Autre'),
    ]

    nom        = models.CharField(max_length=100, verbose_name='Nom complet')
    email      = models.EmailField(verbose_name='Email')
    sujet      = models.CharField(max_length=20, choices=SUJET_CHOICES,
                                  default='general', verbose_name='Sujet')
    message    = models.TextField(max_length=3000, verbose_name='Message')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_read    = models.BooleanField(default=False, verbose_name='Lu')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom} — {self.get_sujet_display()}"
