from django.db import models
from django.utils import timezone
from accounts.models import Professor, Student


class Cours(models.Model):
    """Modèle pour les cours"""
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('archive', 'Archivé'),
        ('brouillon', 'Brouillon'),
    ]
    
    SEMESTRE_CHOICES = [
        ('1', 'Semestre 1'),
        ('2', 'Semestre 2'),
        ('3', 'Semestre 3'),
    ]
    
    # Lien avec le professeur existant
    professeur = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        related_name='cours_enseignes',
        verbose_name='Professeur'
    )
    
    # Informations du cours
    code = models.CharField('Code du cours', max_length=20, unique=True)
    nom = models.CharField('Nom du cours', max_length=200)
    description = models.TextField('Description', blank=True)
    credits = models.IntegerField('Crédits', default=3)
    
    # Étudiants inscrits
    etudiants = models.ManyToManyField(
        Student,
        related_name='cours_inscrits',
        verbose_name='Étudiants',
        blank=True
    )
    
    # Détails académiques
    semestre = models.CharField('Semestre', max_length=1, choices=SEMESTRE_CHOICES)
    annee_academique = models.CharField('Année académique', max_length=9)  # Ex: 2024-2025
    
    # Statut et dates
    statut = models.CharField('Statut', max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_debut = models.DateField('Date de début', null=True, blank=True)
    date_fin = models.DateField('Date de fin', null=True, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)
    date_modification = models.DateTimeField('Date de modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['-date_creation']
        unique_together = ['code', 'annee_academique']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    @property
    def nombre_etudiants(self):
        """Retourne le nombre d'étudiants inscrits"""
        return self.etudiants.count()
    
    @property
    def nom_professeur(self):
        """Retourne le nom complet du professeur"""
        return self.professeur.user.get_full_name()


class Soumission(models.Model):
    """Modèle pour les soumissions des étudiants"""
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('evaluee', 'Évaluée'),
        ('retard', 'En retard'),
    ]
    
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='soumissions',
        verbose_name='Cours'
    )
    etudiant = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='soumissions',
        verbose_name='Étudiant'
    )
    
    # Informations de la soumission
    titre = models.CharField('Titre', max_length=200)
    description = models.TextField('Description', blank=True)
    fichier = models.FileField('Fichier', upload_to='soumissions/%Y/%m/')
    
    # Évaluation
    note = models.DecimalField(
        'Note',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    note_max = models.DecimalField(
        'Note maximale',
        max_digits=5,
        decimal_places=2,
        default=100
    )
    commentaire = models.TextField('Commentaire', blank=True)
    
    # Statut et dates
    statut = models.CharField('Statut', max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_soumission = models.DateTimeField('Date de soumission', auto_now_add=True)
    date_limite = models.DateTimeField('Date limite', null=True, blank=True)
    date_evaluation = models.DateTimeField('Date d\'évaluation', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Soumission'
        verbose_name_plural = 'Soumissions'
        ordering = ['-date_soumission']
    
    def __str__(self):
        return f"{self.titre} - {self.etudiant.user.get_full_name()}"
    
    @property
    def est_en_retard(self):
        """Vérifie si la soumission est en retard"""
        if self.date_limite:
            return self.date_soumission > self.date_limite
        return False
    
    @property
    def nom_etudiant(self):
        """Retourne le nom de l'étudiant"""
        return self.etudiant.user.get_full_name()


class EvenementCalendrier(models.Model):
    """Modèle pour les événements du calendrier"""
    
    TYPE_CHOICES = [
        ('cours', 'Cours'),
        ('examen', 'Examen'),
        ('devoir', 'Devoir'),
        ('reunion', 'Réunion'),
        ('autre', 'Autre'),
    ]
    
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='evenements',
        verbose_name='Cours'
    )
    
    # Informations de l'événement
    titre = models.CharField('Titre', max_length=200)
    description = models.TextField('Description', blank=True)
    type_evenement = models.CharField('Type', max_length=20, choices=TYPE_CHOICES)
    
    # Dates et lieu
    date_debut = models.DateTimeField('Date de début')
    date_fin = models.DateTimeField('Date de fin')
    lieu = models.CharField('Lieu', max_length=200, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'
        ordering = ['date_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y')}"


class Message(models.Model):
    """Modèle pour les messages entre professeurs et étudiants"""
    
    expediteur = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        related_name='messages_envoyes',
        verbose_name='Expéditeur',
        null=True,
        blank=True
    )
    destinataire = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        related_name='messages_recus',
        verbose_name='Destinataire'
    )
    
    # Contenu du message
    sujet = models.CharField('Sujet', max_length=200)
    contenu = models.TextField('Contenu')
    
    # Statut
    lu = models.BooleanField('Lu', default=False)
    date_envoi = models.DateTimeField('Date d\'envoi', auto_now_add=True)
    date_lecture = models.DateTimeField('Date de lecture', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-date_envoi']
    
    def __str__(self):
        return f"{self.sujet} - {self.date_envoi.strftime('%d/%m/%Y')}"
    
    def marquer_comme_lu(self):
        """Marque le message comme lu"""
        if not self.lu:
            self.lu = True
            self.date_lecture = timezone.now()
            self.save()


class ProjetRecherche(models.Model):
    """Modèle pour les projets de recherche"""
    
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('revision', 'En révision'),
        ('termine', 'Terminé'),
        ('abandonne', 'Abandonné'),
    ]
    
    responsable = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        related_name='projets_recherche',
        verbose_name='Responsable'
    )
    
    # Informations du projet
    titre = models.CharField('Titre', max_length=300)
    description = models.TextField('Description')
    domaine = models.CharField('Domaine de recherche', max_length=200)
    
    # Dates
    date_debut = models.DateField('Date de début')
    date_fin_prevue = models.DateField('Date de fin prévue', null=True, blank=True)
    date_fin_reelle = models.DateField('Date de fin réelle', null=True, blank=True)
    
    # Statut et budget
    statut = models.CharField('Statut', max_length=20, choices=STATUT_CHOICES, default='en_cours')
    budget = models.DecimalField(
        'Budget',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Collaborateurs
    collaborateurs = models.ManyToManyField(
        Professor,
        related_name='projets_collabores',
        verbose_name='Collaborateurs',
        blank=True
    )
    
    # Métadonnées
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)
    date_modification = models.DateTimeField('Date de modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Projet de recherche'
        verbose_name_plural = 'Projets de recherche'
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.titre
    
    @property
    def duree_jours(self):
        """Calcule la durée du projet en jours"""
        if self.date_fin_reelle:
            return (self.date_fin_reelle - self.date_debut).days
        elif self.date_fin_prevue:
            return (self.date_fin_prevue - self.date_debut).days
        return None