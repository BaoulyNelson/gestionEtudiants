from django.db import models
from django.utils.text import slugify
import random
import string
from django.utils import timezone
from accounts.models import User


def generate_unique_slug(instance, model, slug_field='slug'):
    """
    Génère un slug unique pour une instance de modèle donné.
    """
    slug = slugify(instance.titre)[:200]
    unique_slug = slug
    num = 1
    ModelClass = model.__class__ if isinstance(model, models.Model) else model

    while ModelClass.objects.filter(**{slug_field: unique_slug}).exclude(pk=instance.pk).exists():
        unique_slug = f"{slug[:200 - len(str(num)) - 1]}-{num}"
        num += 1
    return unique_slug


class Article(models.Model):
    titre = models.CharField(max_length=200, help_text="Le titre de l'article")
    contenu = models.TextField(help_text="Le contenu de l'article")
    auteur = models.CharField(max_length=100, default="FASCH")
    date_publication = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='articles/', null=True, blank=True)
    est_active = models.BooleanField(default=True, help_text="Indique si l'article est actif ou non")
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug or self._state.adding:
            self.slug = generate_unique_slug(self, Article)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre

    def resume(self):
        return self.contenu[:200] + "..." if len(self.contenu) > 200 else self.contenu


from django.utils import timezone

class Evenement(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    image = models.ImageField(upload_to='evenements/', null=True, blank=True)
    lieu = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.slug or self._state.adding:
            self.slug = generate_unique_slug(self, Evenement)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre

    def get_status(self):
        now = timezone.now()
        if self.date_debut > now:
            return "À venir"
        elif self.date_debut <= now <= self.date_fin:
            return "En cours"
        else:
            return "Terminé"



class Annonce(models.Model):
    titre = models.CharField(max_length=255)
    contenu = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    est_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='annonces/', null=True, blank=True)
    organisateur = models.CharField(max_length=255, null=True, blank=True, default="FASCH")
    lieu = models.CharField(max_length=255, null=True, blank=True)
    date_evenement = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug or self._state.adding:
            self.slug = generate_unique_slug(self, Annonce)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre

    def is_active(self):
        return self.est_active





    
    
class Livre(models.Model):
    titre = models.CharField(max_length=200)
    auteur = models.CharField(max_length=100)
    annee = models.IntegerField()
    resume = models.TextField()
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True,editable=False)
    def __str__(self):
        return self.titre


class Personnel(models.Model):
    POSTE_CHOICES = [
        ('doyen', 'Doyen'),
        ('vice_doyen_acad', 'Vice-Doyen Académique'),
        ('vice_doyen_admin', 'Vice-Doyen Administratif'),
        ('secretaire', 'Secrétaire Général'),
        ('agent_admin', 'Agent Administratif'),
        ('rap', 'Responsable Année Préparatoire'),
        ('chef_dept_socio', 'Chef de Département de Sociologie'),
        ('chef_dept_psy', 'Chef de Département de Psychologie'),
        ('chef_dept_com', 'Chef de Département de Communication Sociale'),
        ('chef_dept_ss', 'Chef de Département de Service Social'),
    ]

    poste = models.CharField(max_length=50, choices=POSTE_CHOICES)
    nom = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='personnel/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True,editable=False)
    class Meta:
        verbose_name = "Membre du personnel"
        verbose_name_plural = "Personnel administratif"
        ordering = ['poste']

    def __str__(self):
        return f"{self.nom} - {self.get_poste_display()}"




class Examen(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Terminé'),
        ('active',    'En cours'),
        ('upcoming',  'À venir'),
    ]

    titre       = models.CharField("Intitulé de l'examen", max_length=255)
    date        = models.DateField("Date de l'examen")
    description = models.TextField("Description", blank=True)
    status      = models.CharField(
        "Statut",
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming'
    )

    class Meta:
        ordering = ['date']
        verbose_name        = "Examen"
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
            self.status = 'completed'
        elif self.date == today:
            self.status = 'active'
        else:
            self.status = 'upcoming'
        super().save(*args, **kwargs)
        
        
        
        

            
            
            

