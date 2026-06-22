from django.db import models
from django.utils.text import slugify
import datetime



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
        ("doyen",            "Doyen"),
        ("vice_doyen_acad",  "Vice-Doyen Académique"),
        ("vice_doyen_admin", "Vice-Doyen Administratif"),
        ("secretaire",       "Secrétaire Général"),
        ("agent_admin",      "Agent Administratif"),
        ("rap",              "Responsable Année Préparatoire"),
        ("chef_dept",        "Chef de Département"),   # ← générique
    ]

    poste = models.CharField(max_length=50, choices=POSTE_CHOICES)

    # Renseigné uniquement si poste == "chef_dept"
    departement = models.ForeignKey(
        "departements.Departement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chefs_personnel",
        verbose_name="Département",
        help_text="Obligatoire uniquement pour le poste Chef de Département",
    )

    nom         = models.CharField(max_length=100)
    description = models.TextField()
    photo       = models.ImageField(upload_to="personnel/", blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name          = "Membre du personnel"
        verbose_name_plural   = "Personnel administratif"
        ordering              = ["poste"]

    def __str__(self):
        if self.poste == "chef_dept" and self.departement:
            return f"{self.nom} - Chef de Département ({self.departement.nom})"
        return f"{self.nom} - {self.get_poste_display()}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.poste == "chef_dept" and not self.departement:
            raise ValidationError(
                {"departement": "Un département est obligatoire pour le poste Chef de Département."}
            )
        if self.poste != "chef_dept" and self.departement:
            raise ValidationError(
                {"departement": "Le département ne s'applique qu'au poste Chef de Département."}
            )

class Examen(models.Model):
    CHOIX_TYPE = [
        ("mi_parcours", "Examen de mi-parcours"),
        ("final",       "Examen final"),
        ("rattrapage",  "Rattrapage"),
    ]
    CHOIX_STATUT = [
        ("a_venir",  "À venir"),
        ("en_cours", "En cours"),
        ("termine",  "Terminé"),
    ]

    section_cours = models.ForeignKey(
        'cours.SectionCours',
        on_delete=models.CASCADE,
        related_name='examens',
        verbose_name='Section de cours',
    )
    type_examen = models.CharField(
        'Type', max_length=20,
        choices=CHOIX_TYPE,
        default='final',
    )
    date  = models.DateField('Date')
    heure = models.TimeField('Heure de début', null=True, blank=True)
    salle = models.CharField('Salle', max_length=100, blank=True)
    duree_minutes = models.PositiveIntegerField('Durée (minutes)', default=120)
    description = models.TextField('Remarques', blank=True)
    statut = models.CharField(
        'Statut', max_length=20,
        choices=CHOIX_STATUT,
        default='a_venir',
    )

    class Meta:
        ordering = ['date', 'heure']
        verbose_name = 'Examen'
        verbose_name_plural = 'Examens'

    def __str__(self):
        return (
            f"{self.get_type_examen_display()} — "
            f"{self.section_cours.cours.code} "
            f"Section {self.section_cours.numero_section} "
            f"le {self.date:%d/%m/%Y}"
        )

# models.py (dans une app existante, ex: `portail` ou une nouvelle app `config`)


class NewsletterInscription(models.Model):
    email      = models.EmailField(unique=True)
    nom        = models.CharField(max_length=100, blank=True)
    inscrit_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscription newsletter'
        ordering     = ['-inscrit_le']

    def __str__(self):
        return self.email
    
    
    
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





