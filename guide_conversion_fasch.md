# Guide de Conversion Anglais → Français — Projet FASCH

> **Principe directeur :** On francise tout ce qui est sous notre contrôle (noms de classes, fonctions, variables, URL, templates). On conserve en anglais ce qu'impose Django ou Python (noms de fichiers de configuration, méthodes héritées, attributs de classe Django, migrations).

---

## 0. Ce qui RESTE en anglais (conventions Django/Python)

| Élément | Pourquoi |
|---|---|
| `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `apps.py`, `signals.py`, `middleware.py` | Noms de fichiers imposés par Django |
| `manage.py`, `wsgi.py`, `asgi.py`, `settings.py` | Imposés par le framework |
| `migrations/` et son contenu | Généré automatiquement par Django |
| `__init__.py`, `__str__`, `__call__`, `__init__` | Convention Python |
| `Meta`, `verbose_name`, `ordering`, `unique_together`, `constraints` | Attributs internes Django |
| `clean()`, `save()`, `full_clean()` | Méthodes héritées Django |
| `is_active`, `is_staff`, `is_superuser`, `email`, `first_name`, `last_name`, `password` | Champs hérités de `AbstractUser` — ne PAS renommer |
| `USERNAME_FIELD`, `REQUIRED_FIELDS` | Constantes Django |
| `objects` (manager par défaut) | Django ORM |
| `request`, `request.user`, `request.method`, `request.GET`, `request.POST` | Objet HTTP Django |
| `GET`, `POST` | Méthodes HTTP |
| `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES`, `DEBUG`, `SECRET_KEY`, `STATIC_URL`, etc. | Paramètres Django en majuscules |
| `admin/` (URL Django admin) | URL réservée |
| `static/`, `media/` | Dossiers de convention Django |
| `widget_tweaks`, `crispy_forms`, etc. | Bibliothèques tierces |

---

## 1. Renommage des dossiers d'applications

```
applications/accounts/      →  comptes/
applications/departments/   →  departements/
applications/courses/       →  cours/
applications/enrollments/   →  inscriptions/
applications/grades/        →  notes/
```

> Les apps `admissions`, `faculty`, `articles`, `notifications`, `portal` restent telles quelles (déjà en français pour la plupart, et hors de l'arborescence cible).

---

## 2. `configuration/settings.py`

### Paramètres à modifier

```python
# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'comptes.Utilisateur'

# Backends d'authentification
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'comptes.backends.AuthentificationEmailOuTelephone',
]

# Apps installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps locales
    'comptes.apps.ComptesConfig',
    'departements',
    'cours',
    'inscriptions',
    'notes',
    'portal',
    'admissions',
    'faculty',
    'articles',
    'notifications',

    # Apps tierces
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_bootstrap5',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'comptes.middleware.ControleurChangementMotDePasse',   # ← renommé
]

# Context processor notifications
# Dans TEMPLATES → OPTIONS → context_processors :
'notifications.contexts.contexte_notifications',    # ← renommé

# URLs Login/Logout
LOGIN_URL = 'comptes:connexion'
LOGIN_REDIRECT_URL = 'tableau_bord'
LOGOUT_REDIRECT_URL = 'accueil'

# Paramètres personnalisés (renommés)
MAX_COURS_PAR_SESSION = 8               # était MAX_COURSES_PER_SESSION
MOT_DE_PASSE_TEMPORAIRE = 'motdepasse123'  # était DEFAULT_TEMP_PASSWORD
ELEMENTS_PAR_PAGE = 20                  # était PAGINATION_PER_PAGE

# Dossier média
MEDIA_ROOT = BASE_DIR / 'media'         # inchangé
# Mettre à jour upload_to dans le modèle : 'profils/' au lieu de 'profiles/'
```

---

## 3. `configuration/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from comptes.views import tableau_bord    # ← import renommé

urlpatterns = [
    path('admin/', admin.site.urls),

    # Page d'accueil
    path('', TemplateView.as_view(template_name="accueil.html"), name='accueil'),
    path('tableau-de-bord/', tableau_bord, name='tableau_bord'),

    # Apps — URLs francisées
    path('comptes/',       include('comptes.urls')),
    path('cours/',         include('cours.urls')),
    path('inscriptions/',  include('inscriptions.urls')),
    path('notes/',         include('notes.urls')),
    path('portal/',        include('portal.urls')),
    path('admissions/',    include('admissions.urls')),
    path('faculty/',       include('faculty.urls')),
    path('departements/',  include('departements.urls')),
    path('articles/',      include('articles.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

---

## 4. Application `comptes/`  *(était `accounts/`)*

### 4.1 `comptes/apps.py`

```python
from django.apps import AppConfig

class ComptesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comptes'
    verbose_name = 'Comptes'

    def ready(self):
        import comptes.signals
```

---

### 4.2 `comptes/models.py` — Tableau des renommages

#### Classe `GestionnaireUtilisateur`  *(était `UserManager`)*

| Avant | Après |
|---|---|
| `class UserManager` | `class GestionnaireUtilisateur` |
| `def create_user` | `def creer_utilisateur` |
| `def create_superuser` | `def creer_superutilisateur` |

> **Note :** `create_user` et `create_superuser` sont appelés par Django en interne (`python manage.py createsuperuser`). Si tu les renommes, tu **dois** surcharger `create_user = creer_utilisateur` dans la classe pour que Django les trouve. Solution plus sûre : garde les noms en anglais pour ces deux méthodes uniquement, et renomme seulement la classe.

---

#### Classe `Utilisateur`  *(était `User`)*

| Avant (champ/méthode) | Après | Note |
|---|---|---|
| `class User(AbstractUser)` | `class Utilisateur(AbstractUser)` | |
| `objects = UserManager()` | `objects = GestionnaireUtilisateur()` | |
| `email` | `email` | **Hérité — ne pas renommer** |
| `first_name` | `first_name` | **Hérité — ne pas renommer** |
| `last_name` | `last_name` | **Hérité — ne pas renommer** |
| `is_active` | `is_active` | **Hérité — ne pas renommer** |
| `role` | `role` | Champ personnalisé — peut rester court |
| `gender` | `genre` | |
| `phone_number` | `numero_telephone` | |
| `address` | `adresse` | |
| `date_of_birth` | `date_naissance` | |
| `profile_picture` | `photo_profil` | + `upload_to='profils/'` |
| `must_change_password` | `doit_changer_mot_de_passe` | |
| `created_at` | `cree_le` | |
| `updated_at` | `modifie_le` | |
| `def is_professor()` | `def est_professeur()` | |
| `def is_student()` | `def est_etudiant()` | |
| `def is_admin_user()` | `def est_admin()` | |
| `def role_display_by_gender()` | `def afficher_role_par_genre()` | |
| Valeur `'PROFESSOR'` dans ROLE_CHOICES | `'PROFESSEUR'` | |
| Valeur `'STUDENT'` | `'ETUDIANT'` | |
| Valeur `'ADMIN'` | `'ADMIN'` | (déjà lisible) |
| Valeur `'SUPERUSER'` | `'SUPERUTILISATEUR'` | |
| Valeur `'M'` / `'F'` dans GENDER_CHOICES | inchangé | Valeurs internes |

---

#### Classe `Etudiant`  *(était `Student`)*

| Avant | Après |
|---|---|
| `class Student(models.Model)` | `class Etudiant(models.Model)` |
| `user = models.OneToOneField(Utilisateur, ..., related_name='student_profile')` | `related_name='profil_etudiant'` |
| `student_number` | `numero_etudiant` |
| `department` | `departement` → ForeignKey vers `departements.Departement` |
| `current_year` | `niveau` |
| `enrollment_date` | `date_inscription` |

---

#### Classe `Professeur`  *(était `Professor`)*

| Avant | Après |
|---|---|
| `class Professor(models.Model)` | `class Professeur(models.Model)` |
| `related_name='professor_profile'` | `related_name='profil_professeur'` |
| `professor_id` | `identifiant_professeur` |
| `department` | `departement` |
| `specialization` | `specialisation` |
| `hire_date` | `date_embauche` |

---

#### Classe `Administrateur`  *(était `Admin`)*

| Avant | Après |
|---|---|
| `class Admin(models.Model)` | `class Administrateur(models.Model)` |
| `related_name='admin_profile'` | `related_name='profil_admin'` |
| `admin_id` | `identifiant_admin` |
| `position` | `poste` |

---

#### Code complet `comptes/models.py`

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


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
    """Modèle utilisateur personnalisé pour FASCH"""

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

    def est_admin(self):
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
        (1, 'Année Préparatoire'),
        (2, 'Deuxième Année'),
        (3, 'Troisième Année'),
        (4, 'Quatrième Année'),
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
    niveau = models.IntegerField('Année actuelle', choices=CHOIX_ANNEE)
    date_inscription = models.DateField("Date d'inscription")

    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['numero_etudiant']

    def __str__(self):
        return f"{self.numero_etudiant} - {self.utilisateur.get_full_name()}"


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
    specialisation = models.CharField('Spécialisation', max_length=200, blank=True)
    date_embauche = models.DateField("Date d'embauche")

    class Meta:
        verbose_name = 'Professeur'
        verbose_name_plural = 'Professeurs'
        ordering = ['identifiant_professeur']

    def __str__(self):
        return f"{self.identifiant_professeur} - {self.utilisateur.get_full_name()}"


class Administrateur(models.Model):
    """Profil administrateur"""

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name='profil_admin'
    )
    identifiant_admin = models.CharField('ID Administrateur', max_length=20, unique=True)
    poste = models.CharField('Poste', max_length=100)

    class Meta:
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'

    def __str__(self):
        return f"{self.identifiant_admin} - {self.utilisateur.get_full_name()}"
```

---

### 4.3 `comptes/backends.py`

```python
# Classe renommée
class AuthentificationEmailOuTelephone(ModelBackend):
    # Corps identique, juste renommer la classe
    # Changer aussi : username → identifiant (variable locale seulement)
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifiant = username  # paramètre Django, on garde username dans la signature
        # ... reste identique ...
```

---

### 4.4 `comptes/middleware.py`

```python
from django.shortcuts import redirect
from django.urls import reverse

class ControleurChangementMotDePasse:
    """Middleware pour forcer le changement de mot de passe temporaire"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.urls_exemptees = [
            reverse('comptes:changer_mot_de_passe'),
            reverse('comptes:deconnexion'),
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.doit_changer_mot_de_passe:
                if not any(request.path.startswith(url) for url in self.urls_exemptees):
                    return redirect('comptes:changer_mot_de_passe')
        response = self.get_response(request)
        return response
```

---

### 4.5 `comptes/signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from .models import Professeur, Etudiant, Administrateur

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def creer_ou_mettre_a_jour_profil(sender, instance, created, **kwargs):
    """Crée le profil lié automatiquement selon le rôle."""

    if instance.role == 'PROFESSEUR':
        Professeur.objects.get_or_create(
            utilisateur=instance,
            defaults={
                'identifiant_professeur': f"PROF{instance.id:04d}",
                'date_embauche': timezone.now().date(),
                'departement': None,
                'specialisation': ''
            }
        )
        if hasattr(instance, 'profil_etudiant'):
            instance.profil_etudiant.delete()
        if hasattr(instance, 'profil_admin'):
            instance.profil_admin.delete()

    elif instance.role == 'ETUDIANT':
        Etudiant.objects.get_or_create(
            utilisateur=instance,
            defaults={
                'numero_etudiant': f"ETU{instance.id:04d}",
                'departement': None,
                'niveau': 1,
                'date_inscription': timezone.now().date()
            }
        )
        if hasattr(instance, 'profil_professeur'):
            instance.profil_professeur.delete()
        if hasattr(instance, 'profil_admin'):
            instance.profil_admin.delete()

    elif instance.role == 'ADMIN':
        Administrateur.objects.get_or_create(
            utilisateur=instance,
            defaults={
                'identifiant_admin': f"ADM{instance.id:04d}",
                'poste': 'Administrateur'
            }
        )
        if hasattr(instance, 'profil_etudiant'):
            instance.profil_etudiant.delete()
        if hasattr(instance, 'profil_professeur'):
            instance.profil_professeur.delete()
```

---

### 4.6 `comptes/forms.py`

| Avant | Après |
|---|---|
| `class LoginForm` | `class FormulaireConnexion` |
| `class ChangePasswordForm` | `class FormulaireChangementMotDePasse` |
| `class UserCreationForm` | `class FormulaireCreationUtilisateur` |
| `class UserUpdateForm` | `class FormulaireModificationUtilisateur` |
| `class StudentCreationForm` | `class FormulaireCreationEtudiant` |
| `class StudentUpdateForm` | `class FormulaireModificationEtudiant` |
| `class ProfessorCreationForm` | `class FormulaireCreationProfesseur` |
| `class ProfessorUpdateForm` | `class FormulaireModificationProfesseur` |
| `class AdminCreationForm` | `class FormulaireCreationAdministrateur` |
| `class UserProfileForm` | `class FormulaireProfilUtilisateur` |

Champs Meta des formulaires : remplacer les noms de champs du modèle renommés.

```python
# Exemple FormulaireCreationUtilisateur
class FormulaireCreationUtilisateur(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = [
            'email', 'first_name', 'last_name', 'role', 'genre',
            'numero_telephone', 'adresse', 'date_naissance',
            'photo_profil', 'is_active'
        ]
        # widgets identiques

class FormulaireModificationEtudiant(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ['departement', 'niveau']

class FormulaireModificationProfesseur(forms.ModelForm):
    class Meta:
        model = Professeur
        fields = ['departement', 'specialisation']
```

---

### 4.7 `comptes/urls.py`

```python
from django.urls import path
from . import views
from django.contrib.auth import views as vues_auth
from django.urls import reverse_lazy

app_name = 'comptes'

urlpatterns = [
    # Authentification
    path('connexion/', views.vue_connexion, name='connexion'),
    path('deconnexion/', views.vue_deconnexion, name='deconnexion'),
    path('changer-mot-de-passe/', views.vue_changer_mot_de_passe, name='changer_mot_de_passe'),
    path('tableau-de-bord/', views.tableau_bord, name='tableau_bord'),

    # Profil
    path('profil/', views.vue_profil, name='profil'),

    # Gestion utilisateurs (admin)
    path('utilisateurs/', views.vue_liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/creer/', views.vue_creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/<int:utilisateur_id>/modifier/', views.vue_modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/<int:utilisateur_id>/basculer/', views.vue_basculer_actif, name='basculer_actif'),
    path('utilisateurs/<int:utilisateur_id>/reinitialiser-mdp/', views.vue_reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),
    path('professeurs/', views.vue_liste_professeurs, name='liste_professeurs'),
    path('etudiants/', views.vue_liste_etudiants, name='liste_etudiants'),
    path('etudiant/<int:pk>/', views.vue_detail_etudiant, name='detail_etudiant'),

    # Réinitialisation mot de passe (Django built-in)
    path('reinitialisation/', vues_auth.PasswordResetView.as_view(
        template_name='inscription/reinitialisation_mdp_formulaire.html',
        success_url=reverse_lazy('comptes:reinitialisation_done')
    ), name='reinitialisation'),
    path('reinitialisation/envoye/', vues_auth.PasswordResetDoneView.as_view(
        template_name='inscription/reinitialisation_mdp_envoye.html'
    ), name='reinitialisation_done'),
    path('reinitialisation/<uidb64>/<token>/', vues_auth.PasswordResetConfirmView.as_view(
        template_name='inscription/reinitialisation_mdp_confirmation.html',
        success_url=reverse_lazy('comptes:reinitialisation_complete')
    ), name='reinitialisation_confirmer'),
    path('reinitialisation/complete/', vues_auth.PasswordResetCompleteView.as_view(
        template_name='inscription/reinitialisation_mdp_complete.html'
    ), name='reinitialisation_complete'),
]
```

---

### 4.8 `comptes/views.py` — Renommage complet

| Avant (fonction) | Après |
|---|---|
| `home_view` | `vue_accueil` |
| `dashboard` | `tableau_bord` |
| `login_view` | `vue_connexion` |
| `logout_view` | `vue_deconnexion` |
| `change_password_view` | `vue_changer_mot_de_passe` |
| `profile_view` | `vue_profil` |
| `user_list_view` | `vue_liste_utilisateurs` |
| `user_create_view` | `vue_creer_utilisateur` |
| `user_update_view` | `vue_modifier_utilisateur` |
| `user_toggle_active_view` | `vue_basculer_actif` |
| `reset_password_view` | `vue_reinitialiser_mot_de_passe` |
| `professor_list_view` | `vue_liste_professeurs` |
| `student_list_view` | `vue_liste_etudiants` |
| `student_detail` | `vue_detail_etudiant` |

**Variables locales et contextes (à changer dans chaque fonction) :**

| Avant (variable locale) | Après |
|---|---|
| `user` (variable locale) | `utilisateur` |
| `student` | `etudiant` |
| `professor` | `professeur` |
| `students` | `etudiants` |
| `professors` | `professeurs` |
| `departments` | `departements` |
| `enrollments` | `inscriptions` |
| `active_enrollments` | `inscriptions_actives` |
| `grades` | `liste_notes` |
| `sections` | `sections` |
| `form` | `formulaire` |
| `profile_form` | `formulaire_profil` |
| `search` | `recherche` |
| `role` | `role` |
| `page_obj` | `page_obj` (garder, utilisé dans templates de pagination) |
| `total_courses` | `total_cours` |
| `completed_courses` | `cours_completes` |
| `gpa` | `moyenne` |
| `total_students` | `total_etudiants` |
| `total_professors` | `total_professeurs` |
| `total_enrollments` | `total_inscriptions` |
| `recent_enrollments` | `inscriptions_recentes` |
| `user_id` (paramètre URL) | `utilisateur_id` |

**Clés de contexte (dict passé aux templates) :**

| Avant (clé) | Après |
|---|---|
| `'user'` | `'utilisateur'` |
| `'student'` | `'etudiant'` |
| `'professor'` | `'professeur'` |
| `'active_enrollments'` | `'inscriptions_actives'` |
| `'total_courses'` | `'total_cours'` |
| `'completed_courses'` | `'cours_completes'` |
| `'gpa'` | `'moyenne'` |
| `'is_student'` | `'est_etudiant'` |
| `'is_professor'` | `'est_professeur'` |
| `'is_admin'` | `'est_admin'` |
| `'sections'` | `'sections'` |
| `'total_sections'` | `'total_sections'` |
| `'total_students'` | `'total_etudiants'` |
| `'departments'` | `'departements'` |
| `'recent_enrollments'` | `'inscriptions_recentes'` |
| `'form'` | `'formulaire'` |
| `'profile_form'` | `'formulaire_profil'` |
| `'user_obj'` | `'utilisateur_obj'` |
| `'role_choices'` | `'choix_roles'` |
| `'current_role'` | `'role_actuel'` |
| `'search'` | `'recherche'` |
| `'roles'` | `'roles'` |

**Imports à mettre à jour dans views.py :**

```python
from .models import Utilisateur, Etudiant, Professeur
from .forms import (
    FormulaireConnexion, FormulaireChangementMotDePasse,
    FormulaireCreationUtilisateur, FormulaireModificationUtilisateur,
    FormulaireModificationEtudiant, FormulaireModificationProfesseur,
    FormulaireProfilUtilisateur
)
from departements.models import Departement
from inscriptions.models import Inscription
from cours.models import Cours, SectionCours
from notes.models import Note
from utilitaires.roles import est_admin  # (voir section 9)
```

**Appels aux méthodes renommées :**

```python
# Avant                                Après
user.is_student()               →  utilisateur.est_etudiant()
user.is_professor()             →  utilisateur.est_professeur()
user.is_admin_user()            →  utilisateur.est_admin()
user.role_display_by_gender()   →  utilisateur.afficher_role_par_genre()
user.must_change_password       →  utilisateur.doit_changer_mot_de_passe
user.student_profile            →  utilisateur.profil_etudiant
user.professor_profile          →  utilisateur.profil_professeur

# Relations renommées
student.enrollments             →  etudiant.inscriptions
student.student_number          →  etudiant.numero_etudiant
professor.course_sections       →  professeur.sections_cours

# Filtres QuerySet
status='ENROLLED'               →  statut='INSCRIT'
status='COMPLETED'              →  statut='COMPLETE'

# Templates rendus — mettre à jour les chemins
'accounts/login.html'                    →  'comptes/connexion.html'
'accounts/change_password.html'          →  'comptes/changer_mot_de_passe.html'
'accounts/profile.html'                  →  'comptes/profil.html'
'accounts/user_list.html'               →  'comptes/liste_utilisateurs.html'
'accounts/user_create.html'             →  'comptes/creer_utilisateur.html'
'accounts/user_update.html'             →  'comptes/modifier_utilisateur.html'
'accounts/student_detail.html'          →  'comptes/detail_etudiant.html'
'accounts/logout_confirm.html'          →  'comptes/confirmation_deconnexion.html'
'dashboards/student_dashboard.html'     →  'tableau_de_bord_etudiant.html'
'dashboards/professor_dashboard.html'   →  'tableau_de_bord_professeur.html'
'dashboards/admin_dashboard.html'       →  'tableau_de_bord_administrateur.html'
'home.html'                             →  'accueil.html'

# URLs nommées (redirect / reverse)
redirect('dashboard')             →  redirect('tableau_bord')
redirect('accounts:user_list')    →  redirect('comptes:liste_utilisateurs')
redirect('accounts:profile')      →  redirect('comptes:profil')
redirect('home')                  →  redirect('accueil')
redirect('accounts:change_password') → redirect('comptes:changer_mot_de_passe')

# Settings renommés
settings.MOT_DE_PASSE_TEMPORAIRE    →  settings.MOT_DE_PASSE_TEMPORAIRE
settings.PAGINATION_PER_PAGE      →  settings.ELEMENTS_PAR_PAGE
```

---

## 5. Application `departements/`  *(était `departments/`)*

### 5.1 `departements/apps.py`

```python
class DepartementsConfig(AppConfig):
    name = 'departements'
    verbose_name = 'Départements'
```

### 5.2 `departements/models.py`

```python
class Departement(models.Model):
    CHOIX_DEPARTEMENT = [
        ('PSYCHO', 'Psychologie'),
        ('COMM', 'Communication Sociale'),
        ('SOCIO', 'Sociologie'),
        ('SERVSOC', 'Service social'),
    ]

    code = models.CharField('Code', max_length=20, unique=True, choices=CHOIX_DEPARTEMENT)
    nom = models.CharField('Nom du département', max_length=100, unique=True)
    description = models.TextField('Description', blank=True)
    chef_departement = models.ForeignKey(
        'comptes.Professeur',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='departement_dirige',
        verbose_name='Chef de département'
    )
    cree_le = models.DateTimeField('Date de création', auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def get_total_etudiants(self):
        return self.etudiants.filter(utilisateur__is_active=True).count()

    def get_total_professeurs(self):
        return self.professeurs.filter(utilisateur__is_active=True).count()
```

### 5.3 `departements/urls.py`

```python
app_name = 'departements'

urlpatterns = [
    path('', views.vue_liste_departements, name='liste'),
    path('<int:departement_id>/cours/', views.cours_par_departement, name='cours_par_departement'),
]
```

### 5.4 `departements/views.py` — Renommages

| Avant | Après |
|---|---|
| `department_list` | `vue_liste_departements` |
| `courses_by_department` | `cours_par_departement` |
| `department_id` (paramètre URL) | `departement_id` |

---

### 5.5 `departements/management/commands/charger_departements.py`
*(était `load_departments.py`)*

```python
# Renommer la classe interne
class Command(BaseCommand):
    help = 'Charger les départements depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument('--fichier', type=str, default='donnees/departements.csv')

    def handle(self, *args, **options):
        chemin_fichier = options['fichier']
        # ... logique identique, variables renommées en français ...
```

---

## 6. Application `cours/`  *(était `courses/`)*

### 6.1 `cours/apps.py`

```python
class CoursConfig(AppConfig):
    name = 'cours'
    verbose_name = 'Cours'
```

### 6.2 `cours/models.py`

```python
class Cours(models.Model):
    CHOIX_ANNEE = [
        (1, 'Année Préparatoire'),
        (2, 'Deuxième Année'),
        (3, 'Troisième Année'),
        (4, 'Quatrième Année'),
    ]

    code = models.CharField('Code du cours', max_length=20, unique=True)
    nom = models.CharField('Nom du cours', max_length=200)
    description = models.TextField('Description', blank=True)
    credits = models.IntegerField('Crédits')
    departement = models.ForeignKey(
        'departements.Departement',
        on_delete=models.CASCADE,
        related_name='cours_departement',
        verbose_name='Département', null=True, blank=True
    )
    niveau = models.IntegerField("Année d'études", choices=CHOIX_ANNEE)
    est_actif = models.BooleanField('Actif', default=True)
    cree_le = models.DateTimeField('Date de création', auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.nom}"


class SectionCours(models.Model):
    CHOIX_JOURS = [
        ('LUNDI', 'Lundi'), ('MARDI', 'Mardi'), ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'), ('VENDREDI', 'Vendredi'), ('SAMEDI', 'Samedi'),
    ]
    CHOIX_SESSION = [
        ('SESSION_1', 'Session 1'),
        ('SESSION_2', 'Session 2'),
    ]
    CHOIX_SEMESTRE = [
        ('AUTOMNE', 'Automne'),
        ('PRINTEMPS', 'Printemps'),
        ('ETE', 'Été'),
    ]

    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='sections', verbose_name='Cours')
    numero_section = models.CharField('Numéro de section', max_length=10)
    professeur = models.ForeignKey(
        'comptes.Professeur',
        on_delete=models.SET_NULL, null=True,
        related_name='sections_cours', verbose_name='Professeur'
    )
    jour_semaine = models.CharField('Jour', max_length=20, choices=CHOIX_JOURS)
    heure_debut = models.TimeField('Heure de début')
    heure_fin = models.TimeField('Heure de fin')
    salle = models.CharField('Salle', max_length=50, blank=True)
    session = models.CharField('Session', max_length=20, choices=CHOIX_SESSION)
    semestre = models.CharField('Semestre', max_length=20, choices=CHOIX_SEMESTRE)
    annee = models.IntegerField('Année académique')
    max_etudiants = models.IntegerField("Nombre maximum d'étudiants", default=30)
    est_ouvert = models.BooleanField('Ouvert aux inscriptions', default=True)
    cree_le = models.DateTimeField('Date de création', auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name = 'Section de cours'
        verbose_name_plural = 'Sections de cours'
        ordering = ['cours__code', 'numero_section']
        constraints = [
            models.UniqueConstraint(
                fields=['cours', 'numero_section', 'professeur', 'session', 'semestre', 'annee'],
                name='unique_section_cours_par_professeur'
            )
        ]

    def __str__(self):
        return f"{self.cours.code}-{self.numero_section} ({self.get_session_display()})"

    def clean(self):
        if self.heure_debut and self.heure_fin:
            if self.heure_debut >= self.heure_fin:
                raise ValidationError("L'heure de début doit être avant l'heure de fin.")

    def get_nombre_inscrits(self):
        return self.inscriptions.filter(statut='INSCRIT').count()

    def est_pleine(self):
        return self.get_nombre_inscrits() >= self.max_etudiants

    def peut_inscrire(self):
        return self.est_ouvert and not self.est_pleine()

    def a_conflit_horaire(self, jour, heure_debut, heure_fin):
        if self.jour_semaine != jour:
            return False
        return not (heure_fin <= self.heure_debut or heure_debut >= self.heure_fin)


class Prerequis(models.Model):
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='prerequis', verbose_name='Cours')
    cours_prerequis = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='requis_pour', verbose_name='Cours prérequis')

    class Meta:
        verbose_name = 'Prérequis'
        verbose_name_plural = 'Prérequis'
        unique_together = ['cours', 'cours_prerequis']

    def __str__(self):
        return f"{self.cours.code} nécessite {self.cours_prerequis.code}"

    def clean(self):
        if self.cours == self.cours_prerequis:
            raise ValidationError("Un cours ne peut pas être son propre prérequis.")
```

### 6.3 `cours/urls.py`

```python
app_name = 'cours'

urlpatterns = [
    path('', views.vue_liste_cours, name='liste_cours'),
    path('<int:cours_id>/', views.vue_detail_cours, name='detail_cours'),
    path('creer/', views.vue_creer_cours, name='creer_cours'),
    path('<int:cours_id>/modifier/', views.vue_modifier_cours, name='modifier_cours'),
    path('<int:cours_id>/supprimer/', views.vue_supprimer_cours, name='supprimer_cours'),

    path('sections/', views.vue_liste_sections, name='liste_sections'),
    path('sections/<int:section_id>/', views.vue_detail_section, name='detail_section'),
    path('sections/creer/', views.vue_creer_section, name='creer_section'),
    path('sections/creer/<int:cours_id>/', views.vue_creer_section, name='creer_section_pour_cours'),
    path('sections/<int:section_id>/modifier/', views.vue_modifier_section, name='modifier_section'),
    path('sections/<int:pk>/supprimer/', views.vue_supprimer_section, name='supprimer_section'),
    path('sections/<int:section_id>/basculer/', views.vue_basculer_section, name='basculer_section'),

    path('mes-cours/', views.vue_mes_cours, name='mes_cours'),
]
```

### 6.4 `cours/views.py` — Renommages des fonctions

| Avant | Après |
|---|---|
| `course_list_view` | `vue_liste_cours` |
| `course_detail_view` | `vue_detail_cours` |
| `course_create_view` | `vue_creer_cours` |
| `course_update_view` | `vue_modifier_cours` |
| `course_delete_view` | `vue_supprimer_cours` |
| `section_list_view` | `vue_liste_sections` |
| `section_detail_view` | `vue_detail_section` |
| `section_create_view` | `vue_creer_section` |
| `section_update_view` | `vue_modifier_section` |
| `section_delete_view` | `vue_supprimer_section` |
| `section_toggle_open_view` | `vue_basculer_section` |
| `my_courses_view` | `vue_mes_cours` |

**Templates à pointer :**

```python
'courses/course_list.html'      →  'cours/liste_cours.html'
'courses/course_detail.html'    →  'cours/detail_cours.html'
'courses/course_form.html'      →  'cours/formulaire_cours.html'
'courses/section_list.html'     →  'cours/liste_sections.html'
'courses/section_detail.html'   →  'cours/detail_section.html'
'courses/section_form.html'     →  'cours/formulaire_section.html'
'courses/my_courses.html'       →  'cours/mes_cours.html'
```

---

## 7. Application `inscriptions/`  *(était `enrollments/`)*

### 7.1 `inscriptions/apps.py`

```python
class InscriptionsConfig(AppConfig):
    name = 'inscriptions'
    verbose_name = 'Inscriptions'
```

### 7.2 `inscriptions/models.py`

```python
class Inscription(models.Model):
    CHOIX_STATUT = [
        ('INSCRIT', 'Inscrit'),
        ('ABANDONNE', 'Abandonné'),
        ('COMPLETE', 'Complété'),
        ('ECHOUE', 'Échoué'),
    ]

    etudiant = models.ForeignKey(
        'comptes.Etudiant', on_delete=models.CASCADE,
        related_name='inscriptions', verbose_name='Étudiant'
    )
    section_cours = models.ForeignKey(
        'cours.SectionCours', on_delete=models.CASCADE,
        related_name='inscriptions', verbose_name='Section de cours'
    )
    statut = models.CharField('Statut', max_length=20, choices=CHOIX_STATUT, default='INSCRIT')
    date_inscription = models.DateTimeField("Date d'inscription", auto_now_add=True)
    date_abandon = models.DateTimeField("Date d'abandon", null=True, blank=True)

    class Meta:
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering = ['-date_inscription']
        unique_together = ['etudiant', 'section_cours']

    def __str__(self):
        return (f"{self.etudiant.numero_etudiant} - "
                f"{self.section_cours.cours.code}-{self.section_cours.numero_section}")

    def clean(self):
        if not self.pk:
            inscriptions_session = Inscription.objects.filter(
                etudiant=self.etudiant,
                section_cours__session=self.section_cours.session,
                section_cours__semestre=self.section_cours.semestre,
                section_cours__annee=self.section_cours.annee,
                statut='INSCRIT'
            ).count()

            from django.conf import settings
            max_cours = getattr(settings, 'MAX_COURS_PAR_SESSION', 8)
            if inscriptions_session >= max_cours:
                raise ValidationError(
                    f"L'étudiant a atteint le maximum de {max_cours} cours pour cette session."
                )
            if not self.section_cours.peut_inscrire():
                raise ValidationError("Cette section n'est pas disponible pour inscription.")

            conflits = Inscription.objects.filter(
                etudiant=self.etudiant,
                section_cours__session=self.section_cours.session,
                section_cours__semestre=self.section_cours.semestre,
                section_cours__annee=self.section_cours.annee,
                section_cours__jour_semaine=self.section_cours.jour_semaine,
                statut='INSCRIT'
            )
            for inscription in conflits:
                section = inscription.section_cours
                if section.a_conflit_horaire(
                    self.section_cours.jour_semaine,
                    self.section_cours.heure_debut,
                    self.section_cours.heure_fin
                ):
                    raise ValidationError(
                        f"Conflit d'horaire avec {section.cours.code}-{section.numero_section}."
                    )


class HistoriqueInscription(models.Model):
    inscription = models.ForeignKey(
        Inscription, on_delete=models.CASCADE,
        related_name='historique', verbose_name='Inscription'
    )
    statut_precedent = models.CharField('Statut précédent', max_length=20)
    nouveau_statut = models.CharField('Nouveau statut', max_length=20)
    modifie_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL,
        null=True, verbose_name='Modifié par'
    )
    modifie_le = models.DateTimeField('Date de modification', auto_now_add=True)
    raison = models.TextField('Raison', blank=True)

    class Meta:
        verbose_name = "Historique d'inscription"
        verbose_name_plural = "Historiques d'inscription"
        ordering = ['-modifie_le']
```

### 7.3 `inscriptions/urls.py`

```python
app_name = 'inscriptions'

urlpatterns = [
    path('disponibles/', views.vue_sections_disponibles, name='sections_disponibles'),
    path('mes-inscriptions/', views.vue_mes_inscriptions, name='mes_inscriptions'),
    path('inscrire/<int:section_id>/', views.vue_inscrire, name='inscrire'),
    path('abandonner/<int:inscription_id>/', views.vue_abandonner_inscription, name='abandonner_inscription'),

    path('liste/', views.vue_liste_inscriptions, name='liste_inscriptions'),
    path('creer/', views.vue_creer_inscription, name='creer_inscription'),
    path('<int:inscription_id>/modifier/', views.vue_modifier_inscription, name='modifier_inscription'),
    path('<int:inscription_id>/supprimer/', views.vue_supprimer_inscription, name='supprimer_inscription'),
    path('<int:inscription_id>/statut/', views.vue_maj_statut_inscription, name='maj_statut_inscription'),
    path('<int:inscription_id>/historique/', views.vue_historique_inscription, name='historique_inscription'),
]
```

### 7.4 `inscriptions/views.py` — Renommages des fonctions

| Avant | Après |
|---|---|
| `available_sections_view` | `vue_sections_disponibles` |
| `my_enrollments_view` | `vue_mes_inscriptions` |
| `enroll_view` | `vue_inscrire` |
| `drop_enrollment_view` | `vue_abandonner_inscription` |
| `enrollment_list_view` | `vue_liste_inscriptions` |
| `enrollment_create_view` | `vue_creer_inscription` |
| `enrollment_update_view` | `vue_modifier_inscription` |
| `enrollment_delete_view` | `vue_supprimer_inscription` |
| `enrollment_update_status_view` | `vue_maj_statut_inscription` |
| `enrollment_history_view` | `vue_historique_inscription` |

**Templates :**

```python
'enrollments/available_sections.html'    →  'inscriptions/sections_disponibles.html'
'enrollments/my_enrollments.html'        →  'inscriptions/mes_inscriptions.html'
'enrollments/enrollment_list.html'       →  'inscriptions/liste_inscriptions.html'
'enrollments/enrollment_history.html'    →  'inscriptions/historique_inscriptions.html'
```

---

## 8. Application `notes/`  *(était `grades/`)*

### 8.1 `notes/apps.py`

```python
class NotesConfig(AppConfig):
    name = 'notes'
    verbose_name = 'Notes'
```

### 8.2 `notes/models.py`

```python
class Note(models.Model):
    inscription = models.OneToOneField(
        'inscriptions.Inscription', on_delete=models.CASCADE,
        related_name='note', verbose_name='Inscription'
    )
    examen_mi_parcours = models.DecimalField('Examen de mi-parcours', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    examen_final = models.DecimalField('Examen final', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    travaux = models.DecimalField('Travaux/Devoirs', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    participation = models.DecimalField('Participation', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    projet = models.DecimalField('Projet', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    note_finale = models.DecimalField('Note finale', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    note_lettre = models.CharField('Note lettre', max_length=2, blank=True)
    commentaires = models.TextField('Commentaires', blank=True)
    note_par = models.ForeignKey('comptes.Professeur', on_delete=models.SET_NULL, null=True,
        related_name='etudiants_notes', verbose_name='Noté par')
    cree_le = models.DateTimeField('Date de création', auto_now_add=True)
    modifie_le = models.DateTimeField('Date de modification', auto_now=True)

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['-modifie_le']

    def calculer_note_finale(self):
        ponderations = {
            'examen_mi_parcours': 0.25,
            'examen_final': 0.35,
            'travaux': 0.20,
            'participation': 0.10,
            'projet': 0.10,
        }
        total = 0
        poids_total = 0
        for composante, poids in ponderations.items():
            valeur = getattr(self, composante)
            if valeur is not None:
                total += float(valeur) * poids
                poids_total += poids
        if poids_total > 0:
            self.note_finale = round(total / poids_total, 2)
        else:
            self.note_finale = None
        if self.note_finale is not None:
            self.note_lettre = self.obtenir_note_lettre(float(self.note_finale))
        return self.note_finale

    @staticmethod
    def obtenir_note_lettre(note):
        if note >= 90: return 'A'
        elif note >= 80: return 'B'
        elif note >= 70: return 'C'
        elif note >= 60: return 'D'
        else: return 'F'

    def save(self, *args, **kwargs):
        self.calculer_note_finale()
        super().save(*args, **kwargs)

    def est_reussi(self):
        if self.note_finale is None:
            return None
        return float(self.note_finale) >= 60


class HistoriqueNote(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='historique', verbose_name='Note')
    composante = models.CharField('Composante', max_length=50)
    ancienne_valeur = models.DecimalField('Ancienne valeur', max_digits=5, decimal_places=2, null=True)
    nouvelle_valeur = models.DecimalField('Nouvelle valeur', max_digits=5, decimal_places=2, null=True)
    modifie_par = models.ForeignKey('comptes.Professeur', on_delete=models.SET_NULL, null=True, verbose_name='Modifié par')
    modifie_le = models.DateTimeField('Date de modification', auto_now_add=True)
    raison = models.TextField('Raison', blank=True)

    class Meta:
        verbose_name = 'Historique de note'
        verbose_name_plural = 'Historiques de notes'
        ordering = ['-modifie_le']


class ReleveNotes(models.Model):
    etudiant = models.ForeignKey(
        'comptes.Etudiant', on_delete=models.CASCADE,
        related_name='releves_notes', verbose_name='Étudiant'
    )
    semestre = models.CharField('Semestre', max_length=20)
    annee = models.IntegerField('Année académique')
    moyenne = models.DecimalField('Moyenne générale', max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(4)], null=True, blank=True)
    credits_tentes = models.IntegerField('Crédits tentés', default=0)
    credits_obtenus = models.IntegerField('Crédits obtenus', default=0)
    genere_le = models.DateTimeField('Date de génération', auto_now=True)

    class Meta:
        verbose_name = 'Relevé de notes'
        verbose_name_plural = 'Relevés de notes'
        ordering = ['-annee', '-semestre']
        unique_together = ['etudiant', 'semestre', 'annee']

    def calculer_moyenne(self):
        inscriptions = self.etudiant.inscriptions.filter(
            section_cours__semestre=self.semestre,
            section_cours__annee=self.annee,
            statut='COMPLETE'
        )
        total_points = 0
        total_credits = 0
        for inscription in inscriptions:
            try:
                note = inscription.note
                if note.note_finale is not None:
                    valeur = float(note.note_finale)
                    if valeur >= 90: points = 4.0
                    elif valeur >= 80: points = 3.0
                    elif valeur >= 70: points = 2.0
                    elif valeur >= 60: points = 1.0
                    else: points = 0.0
                    credits = inscription.section_cours.cours.credits
                    total_points += points * credits
                    total_credits += credits
                    if note.est_reussi():
                        self.credits_obtenus += credits
            except Note.DoesNotExist:
                pass
        self.credits_tentes = total_credits
        self.moyenne = round(total_points / total_credits, 2) if total_credits > 0 else None
        return self.moyenne
```

### 8.3 `notes/urls.py`

```python
app_name = 'notes'

urlpatterns = [
    # Professeurs
    path('sections/', views.vue_sections_professeur, name='sections_professeur'),
    path('section/<int:section_id>/resume/', views.vue_resume_notes, name='resume_notes'),
    path('section/<int:section_id>/saisie/', views.vue_saisie_notes, name='saisie_notes'),
    path('note/<int:note_id>/modifier-prof/', views.vue_modifier_note_prof, name='modifier_note_prof'),
    path('mes-etudiants/', views.vue_mes_etudiants, name='mes_etudiants'),
    path('palmares/', views.vue_palmares, name='palmares'),

    # Étudiants
    path('mes-notes/', views.vue_mes_notes, name='mes_notes'),
    path('releve/', views.vue_releve_notes, name='releve_notes'),
    path('mes-professeurs/', views.vue_mes_professeurs, name='mes_professeurs'),

    # Détails
    path('<int:note_id>/', views.vue_detail_note, name='detail_note'),
    path('section/<int:section_id>/statistiques/', views.vue_statistiques_cours, name='statistiques_cours'),

    # Admin
    path('', views.vue_liste_notes_admin, name='liste_notes_admin'),
    path('<int:note_id>/modifier/', views.vue_modifier_note_admin, name='modifier_note_admin'),
    path('<int:note_id>/supprimer/', views.vue_supprimer_note, name='supprimer_note'),
    path('saisie-masse/', views.vue_saisie_masse_notes, name='saisie_masse_notes'),
    path('recalculer/', views.vue_recalculer_notes, name='recalculer_notes'),
    path('exporter/', views.vue_exporter_notes, name='exporter_notes'),
    path('statistiques/', views.vue_statistiques_notes, name='statistiques_notes'),
    path('generer-releve/<int:etudiant_id>/', views.vue_generer_releve, name='generer_releve'),
    path('moyennes-etudiants/', views.vue_moyennes_etudiants, name='moyennes_etudiants'),
    path('recherche-ajax/', views.vue_recherche_ajax_notes, name='recherche_ajax_notes'),
]
```

### 8.4 `notes/views.py` — Renommages des fonctions

| Avant | Après |
|---|---|
| `professor_sections_view` | `vue_sections_professeur` |
| `grades_summary_view` | `vue_resume_notes` |
| `grade_entry_view` | `vue_saisie_notes` |
| `grade_edit_professor` | `vue_modifier_note_prof` |
| `my_students_view` | `vue_mes_etudiants` |
| `palmares_view` | `vue_palmares` |
| `my_grades_view` | `vue_mes_notes` |
| `transcript_view` | `vue_releve_notes` |
| `my_professors_view` | `vue_mes_professeurs` |
| `grade_detail_view` | `vue_detail_note` |
| `course_statistics_view` | `vue_statistiques_cours` |
| `grade_list_view` | `vue_liste_notes_admin` |
| `grade_edit` | `vue_modifier_note_admin` |
| `grade_delete` | `vue_supprimer_note` |
| `grade_bulk_entry` | `vue_saisie_masse_notes` |
| `grade_recalculate` | `vue_recalculer_notes` |
| `grade_export` | `vue_exporter_notes` |
| `grade_statistics` | `vue_statistiques_notes` |
| `generate_transcript_view` | `vue_generer_releve` |
| `students_gpa_view` | `vue_moyennes_etudiants` |
| `grade_search_ajax` | `vue_recherche_ajax_notes` |

**Correspondance des noms de champs dans les filtres QuerySet :**

```python
# Avant                                     Après
Grade.objects.filter(...)              →  Note.objects.filter(...)
enrollment__student=student            →  inscription__etudiant=etudiant
enrollment__status='COMPLETED'         →  inscription__statut='COMPLETE'
course_section__course                 →  section_cours__cours
final_grade                            →  note_finale
letter_grade                           →  note_lettre
graded_by                              →  note_par
comments                               →  commentaires
midterm_exam                           →  examen_mi_parcours
final_exam                             →  examen_final
assignments                            →  travaux
project                                →  projet
```

**Templates :**

```python
'grades/my_grades.html'          →  'notes/mes_notes.html'
'grades/grade_entry.html'        →  'notes/saisie_notes.html'
'grades/grade_list.html'         →  'notes/liste_notes.html'
'grades/grade_detail.html'       →  'notes/detail_note.html'
'grades/professor_sections.html' →  'notes/sections_professeur.html'
'grades/transcript.html'         →  'notes/releve_notes.html'
'grades/course_statistics.html'  →  'notes/statistiques_cours.html'
'grades/grades_summary.html'     →  'notes/resume_notes.html'
```

---

## 9. `utilitaires/roles.py`  *(était `utils/roles.py`)*

```python
def est_professeur(utilisateur):
    """Vérifie si l'utilisateur est un professeur ou superutilisateur"""
    return utilisateur.is_authenticated and (
        utilisateur.is_superuser or utilisateur.est_professeur()
    )

def est_etudiant(utilisateur):
    """Vérifie si l'utilisateur est un étudiant"""
    return utilisateur.is_authenticated and utilisateur.est_etudiant()

def est_admin(utilisateur):
    """Vérifie si l'utilisateur est administrateur ou superutilisateur"""
    return utilisateur.is_authenticated and (
        utilisateur.is_superuser or utilisateur.est_admin()
    )
```

> **Important :** mettre à jour tous les imports dans les vues :
> ```python
> from utilitaires.roles import est_admin, est_professeur, est_etudiant
> ```
> Et les décorateurs :
> ```python
> @user_passes_test(est_admin)
> @user_passes_test(est_professeur)
> ```

---

## 10. Notifications — Mises à jour requises

### `notifications/contexts.py`

```python
def contexte_notifications(request):   # était notifications_context
    if request.user.is_authenticated:
        notifications_non_lues = Notification.objects.filter(
            utilisateur=request.user, est_lue=False
        )
        return {'notifications_non_lues': notifications_non_lues}
    return {'notifications_non_lues': None}
```

### `notifications/signals.py` — Imports à mettre à jour

```python
from notes.models import Note                     # était grades.models → Grade
from notifications.utils import _envoyer_notification_note

@receiver(pre_save, sender=Note)                  # était Grade
def sauvegarder_ancienne_note(sender, instance, **kwargs):
    if instance.pk:
        try:
            ancienne = Note.objects.get(pk=instance.pk)  # était Grade
            instance._ancienne_valeurs = {
                'examen_mi_parcours': ancienne.examen_mi_parcours,  # champs renommés
                'examen_final': ancienne.examen_final,
                'travaux': ancienne.travaux,
                'participation': ancienne.participation,
                'projet': ancienne.projet,
                'note_finale': ancienne.note_finale,
                'note_lettre': ancienne.note_lettre,
            }
        except Note.DoesNotExist:
            instance._ancienne_valeurs = None
```

### `notifications/utils.py` — Noms de champs à mettre à jour

```python
# Correspondance dans le dict noms_champs :
noms_champs = {
    'examen_mi_parcours': 'Examen mi-parcours',
    'examen_final': 'Examen final',
    'travaux': 'Travaux/Devoirs',
    'participation': 'Participation',
    'projet': 'Projet',
    'note_finale': 'Note finale',
    'note_lettre': 'Note lettre',
}

# Accès aux relations renommées :
cours = note.inscription.section_cours.cours         # était enrollment.course_section.course
utilisateur = etudiant.utilisateur                   # était etudiant.user
note.inscription.section_cours.cours.code            # était course_section.course.code
note.est_reussi()                                    # était note.is_passing()
note.note_par.utilisateur.get_full_name()            # était graded_by.user.get_full_name()
note.commentaires                                    # était note.comments
note.note_finale                                     # était final_grade
note.note_lettre                                     # était letter_grade
```

---

## 11. `admin.py` — Mises à jour dans chaque app

### `comptes/admin.py`

```python
from .models import Utilisateur, Etudiant, Professeur, Administrateur

@admin.register(Utilisateur)
class AdministrateurUtilisateur(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'genre', 'numero_telephone', 'is_active', 'cree_le']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'numero_telephone']
    ordering = ['-cree_le']
```

---

## 12. Commandes de gestion — Renommages

| Avant (fichier) | Après |
|---|---|
| `accounts/management/commands/load_professors.py` | `comptes/management/commands/charger_professeurs.py` |
| `accounts/management/commands/load_students.py` | `comptes/management/commands/charger_etudiants.py` |
| `courses/management/commands/load_courses.py` | `cours/management/commands/charger_cours.py` |
| `courses/management/commands/load_sections.py` | `cours/management/commands/charger_sections.py` |
| `departments/management/commands/load_departments.py` | `departements/management/commands/charger_departements.py` |
| `enrollments/management/commands/load_enrollments.py` | `inscriptions/management/commands/charger_inscriptions.py` |
| `grades/management/commands/load_grades.py` | `notes/management/commands/charger_notes.py` |

Nouvelles commandes à appeler :

```bash
python manage.py charger_departements --fichier donnees/departements.csv
python manage.py charger_cours       --fichier donnees/cours.csv
python manage.py charger_sections    --fichier donnees/sections.csv
python manage.py charger_professeurs --fichier donnees/professeurs.csv
python manage.py charger_etudiants   --fichier donnees/etudiants.csv
python manage.py charger_inscriptions --fichier donnees/inscriptions.csv
python manage.py charger_notes       --fichier donnees/notes.csv
```

---

## 13. Templates — Renommages complets

### Structure cible `templates/`

```
templates/
├── accueil.html                              (était home.html)
├── base.html                                 (inchangé)
├── tableau_de_bord_etudiant.html            (était dashboards/student_dashboard.html)
├── tableau_de_bord_professeur.html          (était dashboards/professor_dashboard.html)
├── tableau_de_bord_administrateur.html      (était dashboards/admin_dashboard.html)
├── comptes/
│   ├── connexion.html                        (était accounts/login.html)
│   ├── confirmation_deconnexion.html         (était accounts/logout_confirm.html)
│   ├── changer_mot_de_passe.html            (était accounts/change_password.html)
│   ├── profil.html                           (était accounts/profile.html)
│   ├── liste_utilisateurs.html              (était accounts/user_list.html)
│   ├── creer_utilisateur.html               (était accounts/user_create.html)
│   ├── modifier_utilisateur.html            (était accounts/user_update.html)
│   └── detail_etudiant.html                 (était accounts/student_detail.html)
├── cours/
│   ├── liste_cours.html                     (était courses/course_list.html)
│   ├── detail_cours.html                    (était courses/course_detail.html)
│   ├── formulaire_cours.html                (était courses/course_form.html)
│   ├── liste_sections.html                  (était courses/section_list.html)
│   ├── detail_section.html                  (était courses/section_detail.html)
│   ├── formulaire_section.html              (était courses/section_form.html)
│   └── mes_cours.html                       (était courses/my_courses.html)
├── inscriptions/
│   ├── mes_inscriptions.html                (était enrollments/my_enrollments.html)
│   ├── sections_disponibles.html            (était enrollments/available_sections.html)
│   ├── liste_inscriptions.html              (était enrollments/enrollment_list.html)
│   └── historique_inscriptions.html        (était enrollments/enrollment_history.html)
├── notes/
│   ├── mes_notes.html                       (était grades/my_grades.html)
│   ├── saisie_notes.html                    (était grades/grade_entry.html)
│   ├── liste_notes.html                     (était grades/grade_list.html)
│   ├── detail_note.html                     (était grades/grade_detail.html)
│   ├── sections_professeur.html             (était grades/professor_sections.html)
│   ├── releve_notes.html                    (était grades/transcript.html)
│   └── statistiques_cours.html             (était grades/course_statistics.html)
└── partials/                                (inchangé)
```

### Variables de contexte dans les templates

Dans **tous** les templates, remplacer les variables de contexte :

```html
<!-- Utilisateur -->
{{ user }}                  →  {{ utilisateur }}
{{ user.student_profile }}  →  {{ utilisateur.profil_etudiant }}
{{ is_student }}            →  {{ est_etudiant }}
{{ is_professor }}          →  {{ est_professeur }}
{{ is_admin }}              →  {{ est_admin }}

<!-- Données -->
{{ form }}                  →  {{ formulaire }}
{{ profile_form }}          →  {{ formulaire_profil }}
{{ gpa }}                   →  {{ moyenne }}
{{ total_courses }}         →  {{ total_cours }}
{{ total_students }}        →  {{ total_etudiants }}
{{ active_enrollments }}    →  {{ inscriptions_actives }}
{{ recent_enrollments }}    →  {{ inscriptions_recentes }}
{{ departments }}           →  {{ departements }}
{{ search }}                →  {{ recherche }}
{{ role_choices }}          →  {{ choix_roles }}
{{ current_role }}          →  {{ role_actuel }}

<!-- URL nommées dans les templates -->
{% url 'accounts:login' %}                 →  {% url 'comptes:connexion' %}
{% url 'accounts:logout' %}                →  {% url 'comptes:deconnexion' %}
{% url 'accounts:profile' %}               →  {% url 'comptes:profil' %}
{% url 'accounts:user_list' %}             →  {% url 'comptes:liste_utilisateurs' %}
{% url 'accounts:user_update' user.id %}   →  {% url 'comptes:modifier_utilisateur' utilisateur.id %}
{% url 'accounts:change_password' %}       →  {% url 'comptes:changer_mot_de_passe' %}
{% url 'courses:course_list' %}            →  {% url 'cours:liste_cours' %}
{% url 'courses:my_courses' %}             →  {% url 'cours:mes_cours' %}
{% url 'courses:section_detail' s.id %}    →  {% url 'cours:detail_section' s.id %}
{% url 'enrollments:my_enrollments' %}     →  {% url 'inscriptions:mes_inscriptions' %}
{% url 'enrollments:available_sections' %} →  {% url 'inscriptions:sections_disponibles' %}
{% url 'grades:my_grades' %}               →  {% url 'notes:mes_notes' %}
{% url 'grades:transcript' %}              →  {% url 'notes:releve_notes' %}
{% url 'grades:professor_sections' %}      →  {% url 'notes:sections_professeur' %}
{% url 'dashboard' %}                      →  {% url 'comptes:tableau_bord' %}
{% url 'home' %}                           →  {% url 'accueil' %}

<!-- Accès aux champs renommés -->
{{ enrollment.course_section.course.name }}  →  {{ inscription.section_cours.cours.nom }}
{{ enrollment.status }}                       →  {{ inscription.statut }}
{{ student.student_number }}                  →  {{ etudiant.numero_etudiant }}
{{ grade.final_grade }}                       →  {{ note.note_finale }}
{{ grade.letter_grade }}                      →  {{ note.note_lettre }}
{{ course.name }}                             →  {{ cours.nom }}
{{ section.day_of_week }}                     →  {{ section.jour_semaine }}
{{ department.name }}                         →  {{ departement.nom }}
```

---

## 14. Données CSV — Renommages des colonnes

Le dossier `data/` est renommé en `donnees/`.

| Fichier avant | Fichier après | Colonnes à vérifier/adapter |
|---|---|---|
| `data/departments.csv` | `donnees/departements.csv` | `code`, `name`→`nom`, `description` |
| `data/courses.csv` | `donnees/cours.csv` | `name`→`nom`, `department`→`departement`, `year_level`→`niveau` |
| `data/sections.csv` | `donnees/sections.csv` | `section_number`→`numero_section`, `day_of_week`→`jour_semaine`, etc. |
| `data/professors.csv` | `donnees/professeurs.csv` | `professor_id`→`identifiant_professeur`, `hire_date`→`date_embauche` |
| `data/students.csv` | `donnees/etudiants.csv` | `student_number`→`numero_etudiant`, `enrollment_date`→`date_inscription` |
| `data/enrollments.csv` | `donnees/inscriptions.csv` | `status`→`statut`, valeurs ENROLLED→INSCRIT, etc. |
| `data/grades.csv` | `donnees/notes.csv` | `final_grade`→`note_finale`, `assignments`→`travaux`, etc. |

---

## 15. Ordre d'exécution de la migration

```bash
# 1. Supprimer toutes les migrations existantes (sauf __init__.py)
# Dans chaque app : comptes, departements, cours, inscriptions, notes

# 2. Recréer les migrations
python manage.py makemigrations comptes
python manage.py makemigrations departements
python manage.py makemigrations cours
python manage.py makemigrations inscriptions
python manage.py makemigrations notes

# 3. Appliquer
python manage.py migrate

# 4. Créer le superutilisateur
python manage.py createsuperuser

# 5. Charger les données (dans l'ordre)
python manage.py charger_departements --fichier donnees/departements.csv
python manage.py charger_cours        --fichier donnees/cours.csv
python manage.py charger_sections     --fichier donnees/sections.csv
python manage.py charger_professeurs  --fichier donnees/professeurs.csv
python manage.py charger_etudiants    --fichier donnees/etudiants.csv
python manage.py charger_inscriptions --fichier donnees/inscriptions.csv
python manage.py charger_notes        --fichier donnees/notes.csv
```

---

## 16. Tableau de synthèse global

| Catégorie | Nombre de changements |
|---|---|
| Apps renommées | 5 (comptes, departements, cours, inscriptions, notes) |
| Classes de modèles | 13 renommées |
| Champs de modèles | ~45 renommés |
| Valeurs de statut (DB) | 4 (ENROLLED→INSCRIT, etc.) |
| Classes de formulaires | 10 renommées |
| Fonctions de vues | 35+ renommées |
| URL `name=` | 45+ renommées |
| URL paths | Tous francisés |
| Templates | 25+ renommés + variables internes |
| Commandes de gestion | 7 renommées |
| Classes middleware/backend | 2 renommées |
| Fonctions utilitaires | 3 renommées |

---

> **Rappel final :** Après toutes les modifications, lance `python manage.py check` pour détecter les références cassées avant `python manage.py runserver`.