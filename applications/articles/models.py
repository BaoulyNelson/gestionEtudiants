from django.db import models
from django.utils.text import slugify
from django.utils import timezone

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





class Publication(models.Model):
    """
    Modèle principal couvrant à la fois les recherches vedettes
    et les archives de publications.
    """

    # ── Choix ─────────────────────────────────────────────────────────────────
    CHOIX_TYPE = [
        ('article',     'Article de recherche'),
        ('these',       'Thèse'),
        ('conference',  'Communication de conférence'),
        ('rapport',     'Rapport'),
        ('etudiant',    'Projet étudiant'),
    ]

    CHOIX_STATUT = [
        ('en_cours',  'En cours'),
        ('publie',    'Publié'),
        ('nouveau',   'Nouveau'),
        ('finaliste', 'Finaliste'),
        ('archive',   'Archivé'),
    ]

    CHOIX_LANGUE = [
        ('francais', 'Français'),
        ('creole',   'Kreyòl Ayisyen'),
        ('anglais',  'Anglais'),
    ]

    # ── Identification ─────────────────────────────────────────────────────────
    titre = models.CharField('Titre', max_length=300)
    slug  = models.SlugField('Slug', unique=True, blank=True)

    # ── Catégorisation ─────────────────────────────────────────────────────────
    type_publication = models.CharField('Type', max_length=20, choices=CHOIX_TYPE, default='article')
    statut           = models.CharField('Statut', max_length=20, choices=CHOIX_STATUT, default='publie')
    langue           = models.CharField('Langue', max_length=20, choices=CHOIX_LANGUE, default='francais')

    departement = models.ForeignKey(
        'departements.Departement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='publications',
        verbose_name='Département',
    )

    # ── Contenu ────────────────────────────────────────────────────────────────
    resume  = models.TextField('Résumé')
    contenu = models.TextField('Contenu complet', blank=True)

    # ── Auteurs ────────────────────────────────────────────────────────────────
    # Texte libre pour affichage ("Jean-Claude Moïse, Marie Dupont...")
    auteurs_texte = models.CharField(
        'Auteurs (texte)', max_length=500,
        help_text='Noms séparés par des virgules'
    )
    # Liens optionnels vers les profils internes
    auteur_principal = models.ForeignKey(
        'comptes.Professeur',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='publications',
        verbose_name='Auteur principal (professeur)',
    )
    auteur_etudiant = models.ForeignKey(
        'comptes.Etudiant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='publications',
        verbose_name='Auteur étudiant',
    )

    # ── Référence bibliographique ───────────────────────────────────────────────
    revue            = models.CharField('Revue / Source', max_length=300, blank=True)
    annee_publication = models.IntegerField('Année de publication', null=True, blank=True)
    date_publication  = models.DateField('Date de publication', null=True, blank=True)
    periode_projet    = models.CharField(
        'Période du projet', max_length=50, blank=True,
        help_text='Ex : 2023-2025 ou Septembre 2025'
    )

    # ── Médias ─────────────────────────────────────────────────────────────────
    image      = models.ImageField('Image de couverture', upload_to='publications/images/', null=True, blank=True)
    fichier_pdf = models.FileField('Fichier PDF', upload_to='publications/pdf/', null=True, blank=True)

    # ── Mise en avant ──────────────────────────────────────────────────────────
    est_vedette = models.BooleanField(
        'Recherche vedette', default=False,
        help_text='Afficher dans la section « Recherches Vedettes »'
    )

    # ── Statistiques ───────────────────────────────────────────────────────────
    nombre_vues      = models.PositiveIntegerField('Vues',      default=0)
    nombre_citations = models.PositiveIntegerField('Citations', default=0)

    # ── Métadonnées ────────────────────────────────────────────────────────────
    est_actif  = models.BooleanField('Actif', default=True)
    cree_le    = models.DateTimeField('Créé le',      auto_now_add=True)
    modifie_le = models.DateTimeField('Modifié le',   auto_now=True)

    class Meta:
        verbose_name        = 'Publication'
        verbose_name_plural = 'Publications'
        ordering            = ['-annee_publication', '-cree_le']

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titre)
            slug = base
            n = 1
            while Publication.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def incrementer_vues(self):
        Publication.objects.filter(pk=self.pk).update(nombre_vues=models.F('nombre_vues') + 1)


class MetriqueRecherche(models.Model):
    """
    Chiffres d'impact affichés dans la section
    « Impact de Notre Recherche » (gérables depuis l'admin).
    """
    valeur      = models.CharField('Valeur', max_length=20, help_text='Ex : 847 ou 2 341')
    libelle     = models.CharField('Libellé', max_length=100, help_text='Ex : Publications Totales')
    couleur     = models.CharField(
        'Couleur', max_length=20,
        choices=[
            ('primary',   'Bleu (primary)'),
            ('secondary', 'Rouge (secondary)'),
            ('success',   'Vert (success)'),
            ('accent',    'Violet (accent)'),
        ],
        default='primary'
    )
    icone       = models.CharField('Icône Bootstrap', max_length=50, blank=True,
                                   help_text='Ex : bi-book, bi-journal-text')
    ordre       = models.PositiveSmallIntegerField('Ordre d\'affichage', default=0)
    est_actif   = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name        = 'Métrique de recherche'
        verbose_name_plural = 'Métriques de recherche'
        ordering            = ['ordre']

    def __str__(self):
        return f"{self.valeur} — {self.libelle}"


class Partenariat(models.Model):
    """
    Partenariats affichés dans la section
    « Opportunités de Collaboration ».
    """
    CHOIX_CATEGORIE = [
        ('gouvernement',   'Partenariats Gouvernementaux'),
        ('ong',            'Collaborations ONG'),
        ('international',  'Partenariats Internationaux'),
    ]

    nom        = models.CharField('Nom du partenaire', max_length=200)
    categorie  = models.CharField('Catégorie', max_length=20, choices=CHOIX_CATEGORIE)
    ordre      = models.PositiveSmallIntegerField('Ordre', default=0)
    est_actif  = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name        = 'Partenariat'
        verbose_name_plural = 'Partenariats'
        ordering            = ['categorie', 'ordre']

    def __str__(self):
        return f"{self.get_categorie_display()} — {self.nom}"