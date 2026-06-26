import os
from django.db import models
from django.utils import timezone


def chemin_fichier_devoir(instance, filename):
    """Organise les fichiers joints aux devoirs par devoir."""
    return f"devoirs/cours/{instance.devoir.id}/{filename}"


def chemin_fichier_remise(instance, filename):
    """Organise les fichiers remis par étudiant."""
    return f"devoirs/remises/{instance.remise.devoir.id}/{instance.remise.etudiant.id}/{filename}"


class Devoir(models.Model):
    CHOIX_TYPE = [
        ('FICHIER', 'Remise de fichier'),
        ('TEXTE',   'Réponse texte'),
        ('QCM',     'Questionnaire'),
    ]

    section_cours   = models.ForeignKey(
        'cours.SectionCours',
        on_delete=models.CASCADE,
        related_name='devoirs',
    )
    titre           = models.CharField('Titre', max_length=200)
    description     = models.TextField('Description')
    consignes       = models.TextField('Consignes détaillées', blank=True)
    type_devoir     = models.CharField(
        'Type de devoir', max_length=20,
        choices=CHOIX_TYPE, default='FICHIER',
    )
    date_publication = models.DateTimeField(
        'Date de publication', null=True, blank=True,
        help_text="Laisser vide pour publier immédiatement à la création."
    )
    date_limite     = models.DateTimeField('Date limite de remise')
    points_max      = models.IntegerField('Points maximum', default=100)
    est_publie      = models.BooleanField('Publié', default=False)
    cree_le         = models.DateTimeField(auto_now_add=True)
    cree_par        = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='devoirs_crees',
    )

    class Meta:
        ordering     = ['-date_limite']
        verbose_name = 'Devoir'
        verbose_name_plural = 'Devoirs'

    def __str__(self):
        return f"{self.titre} — {self.section_cours}"

    def est_en_retard(self):
        return timezone.now() > self.date_limite

    def est_visible(self):
        """Vrai si le devoir est publié et la date de publication est passée."""
        if not self.est_publie:
            return False
        if self.date_publication and timezone.now() < self.date_publication:
            return False
        return True

    @property
    def departement(self):
        return self.section_cours.cours.departement

    @property
    def niveau(self):
        return getattr(self.section_cours, 'niveau', None)


class FichierDevoir(models.Model):
    """Fichiers joints à un devoir par le professeur."""
    EXTENSIONS_AUTORISEES = [
        'pdf', 'doc', 'docx', 'ppt', 'pptx',
        'xls', 'xlsx', 'zip', 'rar',
        'jpg', 'jpeg', 'png', 'gif', 'webp',
        'txt', 'mp4', 'mp3',
    ]

    devoir  = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='fichiers')
    fichier = models.FileField('Fichier', upload_to=chemin_fichier_devoir)
    nom     = models.CharField('Nom affiché', max_length=255)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['cree_le']
        verbose_name = 'Fichier joint (devoir)'

    def __str__(self):
        return self.nom

    def extension(self):
        _, ext = os.path.splitext(self.fichier.name)
        return ext.lower().lstrip('.')

    def icone_css(self):
        ext = self.extension()
        mapping = {
            'pdf':  'fa-file-pdf text-danger',
            'doc':  'fa-file-word text-primary',
            'docx': 'fa-file-word text-primary',
            'ppt':  'fa-file-powerpoint text-warning',
            'pptx': 'fa-file-powerpoint text-warning',
            'xls':  'fa-file-excel text-success',
            'xlsx': 'fa-file-excel text-success',
            'zip':  'fa-file-archive text-secondary',
            'rar':  'fa-file-archive text-secondary',
            'jpg':  'fa-file-image text-info',
            'jpeg': 'fa-file-image text-info',
            'png':  'fa-file-image text-info',
            'gif':  'fa-file-image text-info',
        }
        return mapping.get(ext, 'fa-file text-muted')


class Remise(models.Model):
    """Travail rendu par un étudiant pour un devoir."""
    CHOIX_STATUT = [
        ('RENDU',     'Rendu'),
        ('EN_RETARD', 'Rendu en retard'),
        ('NOTE',      'Noté'),
    ]

    devoir           = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='remises')
    etudiant         = models.ForeignKey(
        'comptes.Etudiant',
        on_delete=models.CASCADE,
        related_name='remises',
    )
    contenu          = models.TextField('Réponse texte', blank=True)
    statut           = models.CharField(
        'Statut', max_length=20,
        choices=CHOIX_STATUT, default='RENDU',
    )
    note             = models.DecimalField(
        'Note', max_digits=6, decimal_places=2,
        null=True, blank=True,
    )
    commentaire_prof = models.TextField('Commentaire du professeur', blank=True)
    remis_le         = models.DateTimeField(auto_now_add=True)
    modifie_le       = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together     = ['devoir', 'etudiant']
        ordering            = ['-remis_le']
        verbose_name        = 'Remise'
        verbose_name_plural = 'Remises'

    def __str__(self):
        return f"{self.etudiant} — {self.devoir.titre}"

    def est_en_retard(self):
        return self.statut == 'EN_RETARD'

    def pourcentage_note(self):
        if self.note is not None and self.devoir.points_max:
            return round((float(self.note) / self.devoir.points_max) * 100, 1)
        return None


class FichierRemise(models.Model):
    """Fichiers soumis par l'étudiant dans une remise (multi-fichiers)."""
    remise  = models.ForeignKey(Remise, on_delete=models.CASCADE, related_name='fichiers')
    fichier = models.FileField('Fichier', upload_to=chemin_fichier_remise)
    nom     = models.CharField('Nom du fichier', max_length=255, blank=True)
    taille  = models.PositiveIntegerField('Taille (octets)', default=0)
    ajoute_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['ajoute_le']
        verbose_name = 'Fichier de remise'

    def __str__(self):
        return self.nom or self.fichier.name

    def save(self, *args, **kwargs):
        if self.fichier and not self.nom:
            self.nom = os.path.basename(self.fichier.name)
        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille = self.fichier.size
        super().save(*args, **kwargs)

    def extension(self):
        _, ext = os.path.splitext(self.fichier.name)
        return ext.lower().lstrip('.')

    def icone_css(self):
        ext = self.extension()
        mapping = {
            'pdf':  'fa-file-pdf text-danger',
            'doc':  'fa-file-word text-primary',
            'docx': 'fa-file-word text-primary',
            'ppt':  'fa-file-powerpoint text-warning',
            'pptx': 'fa-file-powerpoint text-warning',
            'zip':  'fa-file-archive text-secondary',
            'jpg':  'fa-file-image text-info',
            'jpeg': 'fa-file-image text-info',
            'png':  'fa-file-image text-info',
        }
        return mapping.get(ext, 'fa-file text-muted')

    def taille_lisible(self):
        t = self.taille
        if t < 1024:
            return f"{t} o"
        elif t < 1024 ** 2:
            return f"{t / 1024:.1f} Ko"
        else:
            return f"{t / 1024 ** 2:.1f} Mo"
