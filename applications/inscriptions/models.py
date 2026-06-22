from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


class Inscription(models.Model):
    """Modèle pour les inscriptions des étudiants aux sections de cours"""

    CHOIX_STATUT = [
        ('INSCRIT',    'Inscrit'),
        ('ABANDONNE',  'Abandonné'),
        ('COMPLETE',   'Complété'),
        ('ECHOUE',     'Échoué'),
    ]
    STATUTS_ACTIFS = ["INSCRIT", "COMPLETE", "ECHOUE"]  # ← ajoute juste cette ligne

    etudiant = models.ForeignKey(
        'comptes.Etudiant',
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name='Étudiant'
    )

    section_cours = models.ForeignKey(
        'cours.SectionCours',
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name='Section de cours'
    )

    statut = models.CharField(
        'Statut',
        max_length=20,
        choices=CHOIX_STATUT,
        default='INSCRIT'
    )

    date_inscription = models.DateTimeField("Date d'inscription", auto_now_add=True)
    date_abandon     = models.DateTimeField("Date d'abandon",     null=True, blank=True)

    class Meta:
        verbose_name        = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering            = ['-date_inscription']
        unique_together     = ['etudiant', 'section_cours']

    def __str__(self):
        return (
            f"{self.etudiant.numero_etudiant} - "
            f"{self.section_cours.cours.code}-"
            f"{self.section_cours.numero_section}"
        )

    def clean(self):
        """Validation des inscriptions"""
        if not self.pk:  # Nouvelle inscription seulement
            max_cours = getattr(settings, 'MAX_COURS_PAR_SESSION', 7)

            # Vérifier le nombre maximum de cours par session
            nb_inscriptions_session = Inscription.objects.filter(
                etudiant=self.etudiant,
                section_cours__session=self.section_cours.session,
                section_cours__semestre=self.section_cours.semestre,
                section_cours__annee=self.section_cours.annee,
                statut='INSCRIT'
            ).count()

            if nb_inscriptions_session >= max_cours:
                raise ValidationError(
                    f"L'étudiant a déjà atteint le maximum de "
                    f"{max_cours} cours pour cette session."
                )

            # Vérifier si la section est ouverte et pas pleine
            if not self.section_cours.inscription_possible():
                raise ValidationError(
                    "Cette section n'est pas disponible pour inscription."
                )

            # Vérifier les conflits d'horaire
            inscriptions_meme_jour = Inscription.objects.filter(
                etudiant=self.etudiant,
                section_cours__session=self.section_cours.session,
                section_cours__semestre=self.section_cours.semestre,
                section_cours__annee=self.section_cours.annee,
                section_cours__jour_semaine=self.section_cours.jour_semaine,
                statut='INSCRIT'
            )

            for inscription in inscriptions_meme_jour:
                section = inscription.section_cours
                if section.conflit_horaire(
                    self.section_cours.jour_semaine,
                    self.section_cours.heure_debut,
                    self.section_cours.heure_fin
                ):
                    raise ValidationError(
                        f"Conflit d'horaire avec le cours "
                        f"{section.cours.code}-{section.numero_section}."
                    )

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        if not self.pk:  # full_clean uniquement à la création
            self.full_clean()
        super().save(*args, **kwargs)


class HistoriqueInscription(models.Model):
    """Historique des modifications d'inscription"""

    inscription = models.ForeignKey(
        Inscription,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name='Inscription'
    )

    statut_precedent = models.CharField('Statut précédent', max_length=20)
    nouveau_statut   = models.CharField('Nouveau statut',   max_length=20)

    modifie_par = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modifié par'
    )

    modifie_le = models.DateTimeField('Date de modification', auto_now_add=True)
    raison     = models.TextField('Raison', blank=True)

    class Meta:
        verbose_name        = "Historique d'inscription"
        verbose_name_plural = "Historiques d'inscription"
        ordering            = ['-modifie_le']

    def __str__(self):
        return (
            f"{self.inscription.etudiant.numero_etudiant} - "
            f"{self.statut_precedent} → {self.nouveau_statut}"
        )