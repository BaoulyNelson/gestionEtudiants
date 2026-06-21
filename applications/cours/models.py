from django.db import models
from django.core.exceptions import ValidationError


class Cours(models.Model):
    """Modèle représentant un cours"""

    # ── Constantes de choix ──────────────────────────────────────────────────

    CHOIX_ANNEE = [
        ('PREPARATOIRE', 'Préparatoire'),
        ('NIVEAU1', 'Niveau I'),
        ('NIVEAU2', 'Niveau II'),
        ('NIVEAU3', 'Niveau III'),
    ]
    # ── Champs ───────────────────────────────────────────────────────────────
    code        = models.CharField('Code du cours', max_length=20, unique=True)
    nom         = models.CharField('Nom du cours',  max_length=200)
    description = models.TextField('Description',   blank=True)
    credits     = models.IntegerField('Crédits')

    departement = models.ForeignKey(
        'departements.Departement',
        on_delete=models.CASCADE,
        related_name='cours',
        verbose_name='Département',
        null=True,
        blank=True,
    )
    niveau = models.CharField(
    max_length=15,
    choices=CHOIX_ANNEE
)
    est_actif    = models.BooleanField('Actif', default=True)

    cree_le    = models.DateTimeField('Date de création',     auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name        = 'Cours'
        verbose_name_plural = 'Cours'
        ordering            = ['code']

    def __str__(self):
        return f"{self.code} - {self.nom}"


class SectionCours(models.Model):
    """Section de cours avec horaire et professeur spécifique"""

    # ── Constantes de choix ──────────────────────────────────────────────────
    CHOIX_JOUR = [
        ('LUNDI',    'Lundi'),
        ('MARDI',    'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI',    'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI',   'Samedi'),
    ]

    CHOIX_SESSION = [
        ('SESSION_1', 'Session 1'),
        ('SESSION_2', 'Session 2'),
    ]

    CHOIX_SEMESTRE = [
        ('AUTOMNE',   'Automne'),
        ('PRINTEMPS', 'Printemps'),
        ('ETE',       'Été'),
    ]

    # ── Champs ───────────────────────────────────────────────────────────────
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Cours',
    )
    numero_section = models.CharField('Numéro de section', max_length=10)

    professeur = models.ForeignKey(
        'comptes.Professeur',          # ← corrigé (était 'comptes.Professor')
        on_delete=models.SET_NULL,
        null=True,
        related_name='sections_cours',
        verbose_name='Professeur',
    )

    # Horaire
    jour_semaine = models.CharField('Jour',           max_length=20, choices=CHOIX_JOUR)
    heure_debut  = models.TimeField('Heure de début')
    heure_fin    = models.TimeField('Heure de fin')
    salle        = models.CharField('Salle',           max_length=50, blank=True)

    # Période académique
    session  = models.CharField('Session',          max_length=20, choices=CHOIX_SESSION)
    semestre = models.CharField('Semestre',         max_length=20, choices=CHOIX_SEMESTRE)
    annee    = models.IntegerField('Année académique')

    # Capacité et accès
    capacite_max = models.IntegerField("Nombre maximum d'étudiants", default=30)
    est_ouverte  = models.BooleanField('Ouvert aux inscriptions',     default=True)

    cree_le    = models.DateTimeField('Date de création',     auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name        = 'Section de cours'
        verbose_name_plural = 'Sections de cours'
        ordering            = ['cours__code', 'numero_section']
        constraints = [
            models.UniqueConstraint(
                fields=['cours', 'numero_section', 'session', 'semestre', 'annee'],
                name='unicite_section_par_periode',
            )
        ]

    def __str__(self):
        return f"{self.cours.code}-{self.numero_section} ({self.get_session_display()})"

    def clean(self):
        """Validation : l'heure de début doit précéder l'heure de fin"""
        if self.heure_debut and self.heure_fin:
            if self.heure_debut >= self.heure_fin:
                raise ValidationError("L'heure de début doit être avant l'heure de fin.")

    # ── Méthodes métier ──────────────────────────────────────────────────────
    # Note : `inscriptions` est le related_name défini dans le modèle Inscription
    # (app inscriptions) — il ne peut pas être renommé ici.

    def nombre_inscrits(self):
        """Retourne le nombre d'étudiants actuellement inscrits (statuts actifs)"""
        from applications.inscriptions.models import Inscription
        return self.inscriptions.filter(statut__in=Inscription.STATUTS_ACTIFS).count()

    def est_pleine(self):
        """Vérifie si la section a atteint sa capacité maximale"""
        return self.nombre_inscrits() >= self.capacite_max

    def inscription_possible(self):
        """Vérifie si un étudiant peut encore s'inscrire"""
        return self.est_ouverte and not self.est_pleine()

    def conflit_horaire(self, jour, heure_debut, heure_fin):
        """Détecte un éventuel chevauchement d'horaire"""
        if self.jour_semaine != jour:
            return False
        return not (heure_fin <= self.heure_debut or heure_debut >= self.heure_fin)


class Prerequis(models.Model):
    """Prérequis associé à un cours"""

    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='prerequis',
        verbose_name='Cours',
    )
    cours_prerequis = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='requis_pour',
        verbose_name='Cours prérequis',
    )

    class Meta:
        verbose_name        = 'Prérequis'
        verbose_name_plural = 'Prérequis'
        unique_together     = ['cours', 'cours_prerequis']

    def __str__(self):
        return f"{self.cours.code} nécessite {self.cours_prerequis.code}"

    def clean(self):
        """Empêche un cours d'être son propre prérequis"""
        if self.cours == self.cours_prerequis:
            raise ValidationError("Un cours ne peut pas être son propre prérequis.")