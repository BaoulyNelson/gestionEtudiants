from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'SUPERUSER')
        extra_fields.setdefault('must_change_password', False)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superuser doit avoir is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Modèle utilisateur personnalisé pour FASCH"""
    
    ROLE_CHOICES = [
        ('SUPERUSER', 'Super Utilisateur'),
        ('ADMIN', 'Administrateur'),
        ('PROFESSOR', 'Professeur'),
        ('STUDENT', 'Étudiant'),
    ]
    
    username = None  # On n'utilise pas le username par défaut
    email = models.EmailField('Email', unique=True)
    
    # Champs communs
    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    role = models.CharField('Rôle', max_length=20, choices=ROLE_CHOICES)
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro doit être au format: '+999999999'. Jusqu'à 15 chiffres."
    )
    phone_number = models.CharField(
        'Téléphone', 
        validators=[phone_regex], 
        max_length=17, 
        blank=True,unique=True
    )
    
    address = models.TextField('Adresse', blank=True)
    date_of_birth = models.DateField('Date de naissance', null=True, blank=True)
    profile_picture = models.ImageField(
        'Photo de profil', 
        upload_to='profiles/', 
        null=True, 
        blank=True
    )
    
    # Gestion des mots de passe
    must_change_password = models.BooleanField(
        'Doit changer le mot de passe', 
        default=True
    )
    
    # Statut
    is_active = models.BooleanField('Actif', default=True)
    
    # Dates
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Date de modification', auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_professor(self):
        return self.role == 'PROFESSOR'
    
    def is_student(self):
        return self.role == 'STUDENT'
    
    def is_admin_user(self):
        return self.role in ['ADMIN', 'SUPERUSER']


class Student(models.Model):
    """Profil étudiant"""
    
    YEAR_CHOICES = [
        (1, 'Année Préparatoire'),
        (2, 'Deuxième Année'),
        (3, 'Troisième Année'),
        (4, 'Quatrième Année'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
    student_number = models.CharField(
        'Numéro étudiant', 
        max_length=20, 
        unique=True
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Département'
    )
    current_year = models.IntegerField('Année actuelle', choices=YEAR_CHOICES)
    enrollment_date = models.DateField('Date d\'inscription')
    
    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['student_number']
    
    def __str__(self):
        return f"{self.student_number} - {self.user.get_full_name()}"


class Professor(models.Model):
    """Profil professeur"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='professor_profile'
    )
    professor_id = models.CharField(
        'ID Professeur', 
        max_length=20, 
        unique=True
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='professors',
        verbose_name='Département principal'
    )
    specialization = models.CharField(
        'Spécialisation', 
        max_length=200, 
        blank=True
    )
    hire_date = models.DateField('Date d\'embauche')
    
    class Meta:
        verbose_name = 'Professeur'
        verbose_name_plural = 'Professeurs'
        ordering = ['professor_id']
    
    def __str__(self):
        return f"{self.professor_id} - {self.user.get_full_name()}"


class Admin(models.Model):
    """Profil administrateur"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='admin_profile'
    )
    admin_id = models.CharField(
        'ID Administrateur', 
        max_length=20, 
        unique=True
    )
    position = models.CharField('Poste', max_length=100)
    
    class Meta:
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'
    
    def __str__(self):
        return f"{self.admin_id} - {self.user.get_full_name()}"