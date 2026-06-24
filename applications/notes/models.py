from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from applications.inscriptions.models import Inscription


class Note(models.Model):
    """Modèle représentant la note d'un étudiant pour une inscription donnée"""

    inscription = models.OneToOneField(
        'inscriptions.Inscription',
        on_delete=models.CASCADE,
        related_name='note',
        verbose_name='Inscription'
    )

    examen_mi_parcours = models.DecimalField(
        'Examen de mi-parcours',
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    examen_final = models.DecimalField(
        'Examen final',
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    travaux = models.DecimalField(
        'Travaux/Devoirs',
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    participation = models.DecimalField(
        'Participation',
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    projet = models.DecimalField(
        'Projet',
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )

    note_finale = models.DecimalField(
        'Note finale',
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    MENTIONS = [
        ('Excellent', 'Excellent'),
        ('Très bien', 'Très bien'),
        ('Bien',      'Bien'),
        ('Passable',  'Passable'),
        ('Échec',     'Échec'),
    ]
    mention = models.CharField(
        'Mention',
        max_length=10,
        choices=MENTIONS,
        blank=True
    )
    commentaires = models.TextField('Commentaires', blank=True)

    note_par = models.ForeignKey(
        'comptes.Professeur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='etudiants_notes',
        verbose_name='Noté par'
    )

    cree_le    = models.DateTimeField('Date de création',     auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name        = 'Note'
        verbose_name_plural = 'Notes'
        ordering            = ['-modifie_le']

    def __str__(self):
        return (
            f"{self.inscription.etudiant.numero_etudiant} - "
            f"{self.inscription.section_cours.cours.code} - "
            f"{self.note_finale or 'Non noté'}"
        )


    @property
    def classe_mention(self):
        mapping = {
            "Excellent": "bg-success",
            "Très bien": "bg-info text-dark",
            "Bien":      "bg-warning text-dark",
            "Passable":  "bg-secondary",
            "Échec":     "bg-danger",
        }
        return mapping.get(self.mention, "bg-light text-dark")

    @staticmethod
    def obtenir_mention(note):
        if note >= 90:   return 'Excellent'
        elif note >= 80: return 'Très bien'
        elif note >= 70: return 'Bien'
        elif note >= 60: return 'Passable'
        else:            return 'Échec'

        
    def calculer_note_finale(self):
        ponderations = {
            'examen_mi_parcours': 0.25,
            'examen_final':       0.35,
            'travaux':            0.20,
            'participation':      0.10,
            'projet':             0.10,
        }
        total, poids_total = 0, 0
        for composante, poids in ponderations.items():
            valeur = getattr(self, composante)
            if valeur is not None:
                total       += float(valeur) * poids
                poids_total += poids

        if poids_total > 0:
            self.note_finale = round(total / poids_total, 2)
        else:
            self.note_finale = None

        if self.note_finale is not None:
            self.mention = self.obtenir_mention(float(self.note_finale))

        return self.note_finale

    def est_recu(self):
        if self.note_finale is None:
            return None
        return float(self.note_finale) >= 60

    def save(self, *args, **kwargs):
        self.calculer_note_finale()
        super().save(*args, **kwargs)
        if self.note_finale is not None and self.inscription.statut == 'INSCRIT':
            Inscription.objects.filter(pk=self.inscription.pk).update(statut='COMPLETE')


class HistoriqueNote(models.Model):
    """Trace toutes les modifications apportées à une note"""

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name='Note'
    )

    composante      = models.CharField('Composante',     max_length=50)
    ancienne_valeur = models.DecimalField('Ancienne valeur', max_digits=5, decimal_places=2, null=True)
    nouvelle_valeur = models.DecimalField('Nouvelle valeur', max_digits=5, decimal_places=2, null=True)

    modifie_par = models.ForeignKey(
        'comptes.Professeur',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modifié par'
    )

    modifie_le = models.DateTimeField('Date de modification', auto_now_add=True)
    raison     = models.TextField('Raison', blank=True)

    class Meta:
        verbose_name        = 'Historique de note'
        verbose_name_plural = 'Historiques de notes'
        ordering            = ['-modifie_le']

    def __str__(self):
        return (
            f"{self.note.inscription.etudiant.numero_etudiant} - "
            f"{self.composante} : {self.ancienne_valeur} → {self.nouvelle_valeur}"
        )


class Bulletin(models.Model):
    """Relevé de notes complet d'un étudiant pour un semestre donné"""

    etudiant = models.ForeignKey(
        'comptes.Etudiant',
        on_delete=models.CASCADE,
        related_name='bulletins',
        verbose_name='Étudiant'
    )

    semestre        = models.CharField('Semestre', max_length=20)
    annee           = models.IntegerField('Année académique')

    gpa = models.DecimalField(
        'Moyenne générale (GPA)',
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )

    credits_tentes  = models.IntegerField('Crédits tentés',  default=0)
    credits_obtenus = models.IntegerField('Crédits obtenus', default=0)
    genere_le       = models.DateTimeField('Date de génération', auto_now=True)

    class Meta:
        verbose_name        = 'Relevé de notes'
        verbose_name_plural = 'Relevés de notes'
        ordering            = ['-annee', '-semestre']
        unique_together     = ['etudiant', 'semestre', 'annee']

    def __str__(self):
        return f"{self.etudiant.numero_etudiant} - {self.semestre} {self.annee}"

    def calculer_gpa(self):
        """Calcule la moyenne générale haïtienne sur 100 pour ce semestre"""
        inscriptions = self.etudiant.inscriptions.filter(
            section_cours__semestre=self.semestre,
            section_cours__annee=self.annee,
            statut__in=['INSCRIT', 'COMPLETE']
        )

        total_notes = 0
        total_cours = 0

        for inscription in inscriptions:
            try:
                note = inscription.note
                if note.note_finale is not None:
                    total_notes += float(note.note_finale)
                    total_cours += 1

                    if note.est_recu():
                        self.credits_obtenus += 1
            except Note.DoesNotExist:
                pass

        self.credits_tentes = total_cours
        self.gpa = round(total_notes / total_cours, 2) if total_cours > 0 else None
        return self.gpa
    
    
    
class NoteDeclaree(models.Model):
    """Note auto-déclarée par l'étudiant, en attente de validation"""

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDEE',    'Validée'),
        ('REJETEE',    'Rejetée'),
    ]

    inscription = models.OneToOneField(
        'inscriptions.Inscription',
        on_delete=models.CASCADE,
        related_name='note_declaree',
    )
    note_declaree       = models.DecimalField(max_digits=5, decimal_places=2)
    commentaire_etudiant = models.TextField(blank=True)
    commentaire_admin    = models.TextField(blank=True)
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')

    declare_le  = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)
    valide_par  = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notes_validees',
    )

    class Meta:
        verbose_name        = 'Note déclarée'
        verbose_name_plural = 'Notes déclarées'

    def __str__(self):
        return f"{self.inscription} — {self.note_declaree} ({self.get_statut_display()})"