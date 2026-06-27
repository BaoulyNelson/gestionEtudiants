from django.db import models
from django.utils.text import slugify
import datetime
from django.core.exceptions import ValidationError
from django.conf import settings


# ============================================================
# À INTÉGRER dans applications/portail/models.py
# Remplacer l'ancien modèle Livre et ajouter Emprunt + Reservation
# ============================================================




class Livre(models.Model):
    """Catalogue de la médiathèque."""

    CHOIX_CATEGORIE = [
        # ── Sciences humaines fondamentales ──────────────────────────────────────
        ('philosophie',        'Philosophie'),
        ('histoire',           'Histoire'),
        ('geographie',         'Géographie'),
        ('histoire_geo',       'Histoire & Géographie'),
        ('archeologie',        'Archéologie'),
        ('anthropologie',      'Anthropologie'),

        # ── Sciences sociales ────────────────────────────────────────────────────
        ('sociologie',         'Sociologie'),
        ('psychologie',        'Psychologie'),
        ('psycho_sociale',     'Psychologie sociale'),
        ('psycho_clinique',    'Psychologie clinique'),
        ('sciences_educ',      'Sciences de l\'éducation'),
        ('travail_social',     'Travail social'),
        ('demographe',         'Démographie'),

        # ── Sciences politiques & juridiques ─────────────────────────────────────
        ('droit',              'Droit'),
        ('droit_public',       'Droit public'),
        ('droit_prive',        'Droit privé'),
        ('droit_international','Droit international'),
        ('science_politique',  'Science politique'),
        ('relations_inter',    'Relations internationales'),

        # ── Économie & Gestion ───────────────────────────────────────────────────
        ('economie',           'Économie'),
        ('economie_dev',       'Économie du développement'),
        ('gestion',            'Gestion & Administration'),
        ('comptabilite',       'Comptabilité & Finance'),

        # ── Langues & Lettres ────────────────────────────────────────────────────
        ('litterature',        'Littérature'),
        ('litterature_fr',     'Littérature française'),
        ('litterature_comp',   'Littérature comparée'),
        ('linguistique',       'Linguistique'),
        ('langues',            'Langues étrangères'),
        ('traduction',         'Traduction & Interprétariat'),

        # ── Communication & Médias ───────────────────────────────────────────────
        ('communication',      'Communication'),
        ('journalisme',        'Journalisme'),
        ('medias_numeriques',  'Médias & Communication numérique'),
        ('relations_pub',      'Relations publiques'),

        # ── Arts & Culture ───────────────────────────────────────────────────────
        ('arts',               'Arts & Culture'),
        ('arts_plastiques',    'Arts plastiques'),
        ('musique',            'Musique'),
        ('cinema',             'Cinéma & Audiovisuel'),
        ('patrimoine',         'Patrimoine culturel'),

        # ── Sciences & Méthodes ──────────────────────────────────────────────────
        ('statistiques',       'Statistiques & Méthodes quantitatives'),
        ('informatique',       'Informatique & Humanités numériques'),
        ('recherche',          'Méthodologie de la recherche'),

        # ── Divers ───────────────────────────────────────────────────────────────
        ('interdisciplinaire', 'Interdisciplinaire'),
        ('autre',              'Autre'),
    ]

    titre           = models.CharField('Titre', max_length=200)
    auteur          = models.CharField('Auteur(s)', max_length=200)
    isbn            = models.CharField('ISBN', max_length=20, blank=True, null=True, unique=True)
    editeur         = models.CharField('Éditeur', max_length=100, blank=True)
    annee           = models.IntegerField('Année de publication')
    categorie       = models.CharField('Catégorie', max_length=30, choices=CHOIX_CATEGORIE, default='autre')
    resume          = models.TextField('Résumé')
    couverture      = models.ImageField('Couverture', upload_to='livres/couvertures/', blank=True, null=True)
    nombre_exemplaires = models.PositiveIntegerField('Nombre d\'exemplaires', default=1)
    date_creation   = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name        = 'Livre'
        verbose_name_plural = 'Livres'
        ordering            = ['titre']

    def __str__(self):
        return f"{self.titre} — {self.auteur}"

    @property
    def exemplaires_disponibles(self):
        """Nombre d'exemplaires actuellement disponibles."""
        empruntes = self.emprunts.filter(statut='en_cours').count()
        return max(0, self.nombre_exemplaires - empruntes)

    @property
    def disponible(self):
        return self.exemplaires_disponibles > 0

    def en_attente_count(self):
        return self.reservations.filter(statut='en_attente').count()


class Emprunt(models.Model):
    """Enregistre chaque emprunt d'un livre par un utilisateur."""

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('rendu',    'Rendu'),
        ('en_retard','En retard'),
    ]

    DUREE_DEFAUT_JOURS = 14  # 2 semaines

    utilisateur     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emprunts',
        verbose_name='Emprunteur',
    )
    livre           = models.ForeignKey(
        Livre,
        on_delete=models.CASCADE,
        related_name='emprunts',
        verbose_name='Livre',
    )
    date_emprunt    = models.DateField('Date d\'emprunt', default=datetime.date.today)
    date_retour_prevue = models.DateField('Date de retour prévue')
    date_retour_effective = models.DateField('Date de retour effective', null=True, blank=True)
    statut          = models.CharField('Statut', max_length=10, choices=STATUT_CHOICES, default='en_cours')
    note_admin      = models.TextField('Note interne', blank=True)

    class Meta:
        verbose_name        = 'Emprunt'
        verbose_name_plural = 'Emprunts'
        ordering            = ['-date_emprunt']

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} — {self.livre.titre} ({self.statut})"

    def save(self, *args, **kwargs):
        # Calcule la date de retour prévue si pas définie
        if not self.date_retour_prevue:
            self.date_retour_prevue = self.date_emprunt + datetime.timedelta(days=self.DUREE_DEFAUT_JOURS)
        # Met à jour le statut automatiquement
        if self.statut == 'en_cours' and self.date_retour_prevue < datetime.date.today():
            self.statut = 'en_retard'
        super().save(*args, **kwargs)

    @property
    def est_en_retard(self):
        if self.statut == 'rendu':
            return False
        return self.date_retour_prevue < datetime.date.today()

    @property
    def jours_retard(self):
        if not self.est_en_retard:
            return 0
        return (datetime.date.today() - self.date_retour_prevue).days

    @property
    def jours_restants(self):
        if self.statut == 'rendu':
            return None
        delta = self.date_retour_prevue - datetime.date.today()
        return delta.days  # négatif si en retard


class Reservation(models.Model):
    """File d'attente quand un livre est indisponible."""

    STATUT_CHOICES = [
        ('en_attente',  'En attente'),
        ('disponible',  'Disponible — à récupérer'),
        ('expiree',     'Expirée'),
        ('annulee',     'Annulée'),
    ]

    DELAI_DISPONIBILITE_JOURS = 3  # L'utilisateur a 3 jours pour récupérer

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Utilisateur',
    )
    livre = models.ForeignKey(
        Livre,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Livre',
    )
    date_reservation  = models.DateTimeField('Date de réservation', auto_now_add=True)
    statut            = models.CharField('Statut', max_length=15, choices=STATUT_CHOICES, default='en_attente')
    date_disponibilite = models.DateField('Disponible jusqu\'au', null=True, blank=True)

    class Meta:
        verbose_name        = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering            = ['date_reservation']
        # Un utilisateur ne peut réserver le même livre qu'une seule fois en attente
        unique_together = [['utilisateur', 'livre']]

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} — {self.livre.titre} ({self.statut})"

    def notifier_disponible(self):
        """Passe la réservation à 'disponible' et fixe la date limite."""
        self.statut = 'disponible'
        self.date_disponibilite = datetime.date.today() + datetime.timedelta(days=self.DELAI_DISPONIBILITE_JOURS)
        self.save()


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





