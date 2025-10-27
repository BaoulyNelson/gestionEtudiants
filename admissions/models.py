

from django.db import models
from django.core.validators import RegexValidator
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from departments.models import Department

class Candidature(models.Model):
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('en_revision', 'En Révision'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]
    
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    nom = models.CharField(max_length=100, verbose_name="Nom de famille")
    email = models.EmailField(verbose_name="Email")
    
    phone_regex = RegexValidator(
        regex=r'^\+?509?\d{8,10}$',
        message="Numéro de téléphone invalide. Format: +509XXXXXXXX"
    )
    telephone = models.CharField(validators=[phone_regex], max_length=15, verbose_name="Téléphone")
    
    # Lien direct vers le département/programme
    programme = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Programme souhaité",
        related_name="candidatures"
    )
    
    lettre_motivation = models.TextField(verbose_name="Lettre de motivation")
    accepte_conditions = models.BooleanField(default=False, verbose_name="Conditions acceptées")
    
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='brouillon')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.programme.name if self.programme else 'N/A'}"



# ==================== MODÈLE STATISTIQUE ====================
class Statistique(models.Model):
    COULEUR_CHOICES = [
        ('primary', 'Bleu Principal'),
        ('secondary', 'Orange Secondaire'),
        ('success', 'Vert Succès'),
        ('accent', 'Rose Accent'),
        ('warning', 'Jaune Attention'),
    ]
    
    valeur = models.CharField(
        max_length=20, 
        verbose_name="Valeur",
        help_text="Ex: 94%, 2,847, 85%"
    )
    label = models.CharField(
        max_length=100, 
        verbose_name="Libellé",
        help_text="Ex: Taux d'Acceptation"
    )
    couleur = models.CharField(
        max_length=20, 
        choices=COULEUR_CHOICES, 
        default='primary',
        verbose_name="Couleur"
    )
    ordre = models.IntegerField(
        default=0, 
        verbose_name="Ordre d'affichage",
        help_text="Les statistiques sont affichées par ordre croissant"
    )
    actif = models.BooleanField(
        default=True, 
        verbose_name="Actif",
        help_text="Décochez pour masquer cette statistique"
    )
    
    class Meta:
        verbose_name = "Statistique"
        verbose_name_plural = "Statistiques"
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.valeur} - {self.label}"


# ==================== MODÈLE AMBASSADEUR ====================
class Ambassadeur(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom complet")
    photo = models.ImageField(
        upload_to='ambassadeurs/', 
        verbose_name="Photo",
        help_text="Photo de profil (recommandé: 400x400px)"
    )
    programme = models.CharField(
        max_length=100, 
        verbose_name="Programme d'études",
        help_text="Ex: Psychologie, Sociologie"
    )
    
    programme = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Programme d'études",
        related_name="ambassadeurs"
    )
    annee = models.CharField(
        max_length=50, 
        verbose_name="Année d'études",
        help_text="Ex: 3ème année, 4ème année"
    )
    temoignage = models.TextField(
        verbose_name="Témoignage",
        help_text="Citation courte de l'ambassadeur"
    )
    
    # Spécialités sous forme de JSONField
    specialites = models.JSONField(
        default=list,
        verbose_name="Spécialités",
        help_text='Liste des tags, ex: ["Psychologie clinique", "Recherche"]'
    )
    
    email = models.EmailField(
        blank=True, 
        null=True, 
        verbose_name="Email de contact"
    )
    
    ordre = models.IntegerField(
        default=0, 
        verbose_name="Ordre d'affichage"
    )
    actif = models.BooleanField(
        default=True, 
        verbose_name="Actif",
        help_text="Décochez pour masquer cet ambassadeur"
    )
    
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ambassadeur Étudiant"
        verbose_name_plural = "Ambassadeurs Étudiants"
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.programme}"


# ==================== MODÈLE FAQ ====================
class FAQ(models.Model):
    CATEGORIE_CHOICES = [
        ('admission', 'Admission'),
        ('financement', 'Financement'),
        ('programmes', 'Departement'),
        ('vie_etudiante', 'Vie Étudiante'),
        ('general', 'Général'),
    ]
    
    question = models.CharField(
        max_length=255, 
        verbose_name="Question"
    )
    reponse = models.TextField(verbose_name="Réponse")
    
    categorie = models.CharField(
        max_length=50,
        choices=CATEGORIE_CHOICES,
        default='general',
        verbose_name="Catégorie"
    )
    
    ordre = models.IntegerField(
        default=0, 
        verbose_name="Ordre d'affichage",
        help_text="Les questions sont affichées par ordre croissant"
    )
    actif = models.BooleanField(
        default=True, 
        verbose_name="Actif",
        help_text="Décochez pour masquer cette question"
    )
    
    nombre_vues = models.IntegerField(
        default=0,
        verbose_name="Nombre de vues",
        editable=False
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Question Fréquente (FAQ)"
        verbose_name_plural = "Questions Fréquentes (FAQ)"
        ordering = ['ordre', 'categorie']
    
    def __str__(self):
        return self.question





# ==================== MODÈLE TYPE DE BOURSE ====================
class TypeBourse(models.Model):
    COULEUR_CHOICES = [
        ('primary', 'Bleu Principal'),
        ('secondary', 'Orange Secondaire'),
        ('success', 'Vert Succès'),
        ('accent', 'Rose Accent'),
    ]
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la bourse",
        help_text="Ex: Bourse d'Excellence Académique"
    )
    
    description = models.TextField(
        verbose_name="Description",
        help_text="Description détaillée de la bourse"
    )
    
    pourcentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pourcentage de réduction",
        help_text="Pourcentage des frais couverts (0-100%)"
    )
    
    nombre_disponible = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre de bourses disponibles"
    )
    
    couleur = models.CharField(
        max_length=20,
        choices=COULEUR_CHOICES,
        default='primary',
        verbose_name="Couleur"
    )
    
    icone_svg = models.TextField(
        verbose_name="Code SVG de l'icône",
        help_text="Code SVG complet de l'icône"
    )
    
    criteres = models.JSONField(
        default=list,
        verbose_name="Critères d'éligibilité",
        help_text='Liste des critères, ex: ["Moyenne ≥ 15/20", "Dossier complet"]'
    )
    
    actif = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    class Meta:
        verbose_name = "Type de Bourse"
        verbose_name_plural = "Types de Bourses"
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.pourcentage}%)"


# ==================== MODÈLE VISITE VIRTUELLE ====================
class VisiteVirtuelle(models.Model):
    titre = models.CharField(
        max_length=100,
        verbose_name="Titre",
        help_text="Ex: Bibliothèque Centrale"
    )
    
    sous_titre = models.CharField(
        max_length=200,
        verbose_name="Sous-titre",
        help_text="Ex: 50,000 ouvrages spécialisés"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    image = models.ImageField(
        upload_to='visites_virtuelles/',
        verbose_name="Image de couverture",
        help_text="Image principale (recommandé: 1200x600px)"
    )
    
    url_visite = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de la visite 360°",
        help_text="Lien vers la visite virtuelle interactive"
    )
    
    couleur = models.CharField(
        max_length=20,
        choices=[
            ('primary', 'Bleu'),
            ('secondary', 'Orange'),
            ('success', 'Vert'),
        ],
        default='primary',
        verbose_name="Couleur du thème"
    )
    
    actif = models.BooleanField(default=True, verbose_name="Active")
    ordre = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        verbose_name = "Visite Virtuelle"
        verbose_name_plural = "Visites Virtuelles"
        ordering = ['ordre', 'titre']
    
    def __str__(self):
        return self.titre


