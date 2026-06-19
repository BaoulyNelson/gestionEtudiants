from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class GestionnaireUtilisateur(BaseUserManager):
    """Manager personnalisé pour le modèle Utilisateur"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        utilisateur = self.model(email=email, **extra_fields)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'SUPERUTILISATEUR')
        extra_fields.setdefault('doit_changer_mot_de_passe', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé pour FASCH

    Convention de nommage :
    - Champs hérités d'AbstractUser (first_name, last_name, is_active,
      is_staff, is_superuser, username, password, last_login, ...) :
      restent en ANGLAIS, ce sont des champs internes Django.
    - Tous les champs ajoutés ici : en FRANÇAIS.
    """

    CHOIX_ROLE = [
        ('SUPERUTILISATEUR', 'Super Utilisateur'),
        ('ADMIN', 'Administrateur'),
        ('PROFESSEUR', 'Professeur'),
        ('ETUDIANT', 'Étudiant'),
    ]
    CHOIX_GENRE = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    username = None
    email = models.EmailField('Email', unique=True)

    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    role = models.CharField('Rôle', max_length=20, choices=CHOIX_ROLE)
    genre = models.CharField('Genre', max_length=1, choices=CHOIX_GENRE, default='M')

    validateur_telephone = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro doit être au format : '+999999999'. Jusqu'à 15 chiffres."
    )
    numero_telephone = models.CharField(
        'Téléphone',
        validators=[validateur_telephone],
        max_length=17,
        blank=True, unique=True, null=True
    )

    adresse = models.TextField('Adresse', blank=True)
    date_naissance = models.DateField('Date de naissance', null=True, blank=True)
    photo_profil = models.ImageField(
        'Photo de profil',
        upload_to='profils/',
        null=True, blank=True
    )

    doit_changer_mot_de_passe = models.BooleanField(
        'Doit changer le mot de passe', default=True
    )

    cree_le = models.DateTimeField('Date de création', auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    objects = GestionnaireUtilisateur()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def est_professeur(self):
        return self.role == 'PROFESSEUR'

    def est_etudiant(self):
        return self.role == 'ETUDIANT'

    def est_administrateur(self):
        return self.role in ['ADMIN', 'SUPERUTILISATEUR']

    def afficher_role_par_genre(self):
        if self.role == 'ETUDIANT':
            return 'Étudiante' if self.genre == 'F' else 'Étudiant'
        elif self.role == 'PROFESSEUR':
            return 'Professeure' if self.genre == 'F' else 'Professeur'
        return self.get_role_display()


class Etudiant(models.Model):
    """Profil étudiant"""

    CHOIX_ANNEE = [
        ('PREPARATOIRE', 'Préparatoire'),
        ('NIVEAU1', 'Niveau I'),
        ('NIVEAU2', 'Niveau II'),
        ('NIVEAU3', 'Niveau III'),
    ]

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name='profil_etudiant'
    )
    numero_etudiant = models.CharField('Numéro étudiant', max_length=20, unique=True)
    departement = models.ForeignKey(
        'departements.Departement',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='etudiants', verbose_name='Département'
    )
    niveau = models.CharField('Niveau actuel', max_length=20, choices=CHOIX_ANNEE)
    date_inscription = models.DateField("Date d'inscription")

    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['numero_etudiant']


    def __str__(self):
        return f"{self.numero_etudiant} - {self.utilisateur.get_full_name()}"

    def clean(self):
        if self.utilisateur.role != 'ETUDIANT':
            raise ValidationError(
                "Le rôle de l'utilisateur doit être 'ETUDIANT' pour créer un profil étudiant."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        
class Professeur(models.Model):
    """Profil professeur"""

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name='profil_professeur'
    )
    identifiant_professeur = models.CharField('ID Professeur', max_length=20, unique=True)
    departement = models.ForeignKey(
        'departements.Departement',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='professeurs', verbose_name='Département principal'
    )
    specialite = models.CharField('Spécialisation', max_length=200, blank=True)
    date_embauche = models.DateField("Date d'embauche")

    class Meta:
        verbose_name = 'Professeur'
        verbose_name_plural = 'Professeurs'
        ordering = ['identifiant_professeur']

    def __str__(self):
        return f"{self.identifiant_professeur} - {self.utilisateur.get_full_name()}"

    def clean(self):
        if self.utilisateur.role != 'PROFESSEUR':
            raise ValidationError(
                "Le rôle de l'utilisateur doit être 'PROFESSEUR' pour créer un profil professeur."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        
        

class Administrateur(models.Model):
    """Profil administrateur"""

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name='profil_admin'
    )
    identifiant_administrateur = models.CharField('ID Administrateur', max_length=20, unique=True)
    poste = models.CharField('Poste', max_length=100)

    class Meta:
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'

    def __str__(self):
        return f"{self.identifiant_administrateur} - {self.utilisateur.get_full_name()}"
    
    def clean(self):
        if self.utilisateur.role not in ['ADMIN', 'SUPERUTILISATEUR']:
            raise ValidationError(
                "Le rôle de l'utilisateur doit être 'ADMIN' ou 'SUPERUTILISATEUR' pour créer un profil administrateur."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)