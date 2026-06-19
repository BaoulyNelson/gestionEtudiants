from django.db import models
from django.utils.text import slugify

from django.utils import timezone


class Livre(models.Model):
    titre = models.CharField(max_length=200)
    auteur = models.CharField(max_length=100)
    annee = models.IntegerField()
    resume = models.TextField()
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.titre


class Personnel(models.Model):
    POSTE_CHOICES = [
        ("doyen", "Doyen"),
        ("vice_doyen_acad", "Vice-Doyen Académique"),
        ("vice_doyen_admin", "Vice-Doyen Administratif"),
        ("secretaire", "Secrétaire Général"),
        ("agent_admin", "Agent Administratif"),
        ("rap", "Responsable Année Préparatoire"),
        ("chef_dept_socio", "Chef de Département de Sociologie"),
        ("chef_dept_psy", "Chef de Département de Psychologie"),
        ("chef_dept_com", "Chef de Département de Communication Sociale"),
        ("chef_dept_ss", "Chef de Département de Service Social"),
    ]

    poste = models.CharField(max_length=50, choices=POSTE_CHOICES)
    nom = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to="personnel/", blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "Membre du personnel"
        verbose_name_plural = "Personnel administratif"
        ordering = ["poste"]

    def __str__(self):
        return f"{self.nom} - {self.get_poste_display()}"


class Examen(models.Model):
    STATUS_CHOICES = [
        ("completed", "Terminé"),
        ("active", "En cours"),
        ("upcoming", "À venir"),
    ]

    titre = models.CharField("Intitulé de l'examen", max_length=255)
    date = models.DateField("Date de l'examen")
    description = models.TextField("Description", blank=True)
    status = models.CharField(
        "Statut", max_length=20, choices=STATUS_CHOICES, default="upcoming"
    )

    class Meta:
        ordering = ["date"]
        verbose_name = "Examen"
        verbose_name_plural = "Examens"

    def __str__(self):
        return f"{self.titre} le {self.date:%d %B %Y}"

    def save(self, *args, **kwargs):
        """
        Recalcule automatiquement `status` en fonction de `date` :
        - date < aujourd'hui  → 'completed'
        - date == aujourd'hui → 'active'
        - date > aujourd'hui  → 'upcoming'
        """
        today = timezone.localdate()
        if self.date < today:
            self.status = "completed"
        elif self.date == today:
            self.status = "active"
        else:
            self.status = "upcoming"
        super().save(*args, **kwargs)


# models.py (dans une app existante, ex: `portail` ou une nouvelle app `config`)



class SiteSettings(models.Model):
    # Infos générales
    nom_etablissement = models.CharField(max_length=100, default="FASCH")
    nom_complet = models.CharField(
        max_length=200, default="Faculté des Sciences Humaines"
    )
    slogan = models.TextField(
        blank=True, default="Depuis 1975, FASCH forme les leaders de demain..."
    )
    annee_fondation = models.PositiveIntegerField(default=1975)

    # Contact
    adresse_ligne1 = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    # Identité visuelle
    logo = models.ImageField(
        upload_to='site/logo/',
        null=True, blank=True,
        verbose_name='Logo'
    )
    logo_small = models.ImageField(
        upload_to='site/logo/',
        null=True, blank=True,
        verbose_name='Logo petit (favicon/topbar)'
    )

    # Signatures officielles
    nom_directeur_etudes = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nom du Directeur des Études'
    )
    titre_directeur_etudes = models.CharField(
        max_length=200, blank=True,
        default='Le Directeur des Études',
        verbose_name='Titre du Directeur des Études'
    )
    signature_directeur = models.ImageField(
        upload_to='site/signatures/',
        null=True, blank=True,
        verbose_name='Signature du Directeur (image)'
    )
    cachet_officiel = models.ImageField(
        upload_to='site/cachets/',
        null=True, blank=True,
        verbose_name='Cachet officiel'
    )
    # Réseaux sociaux
    lien_twitter = models.URLField(blank=True)
    lien_facebook = models.URLField(blank=True)
    lien_linkedin = models.URLField(blank=True)

    # Copyright
    annee_copyright = models.PositiveIntegerField(default=2026)

    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

    def __str__(self):
        return self.nom_etablissement

    @classmethod
    def get(cls):
        """Retourne toujours la première instance (singleton)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
