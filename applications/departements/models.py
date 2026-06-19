from django.db import models


class Departement(models.Model):

    CHOIX_DEPARTEMENT = [
        ("PSY", "Psychologie"),
        ("COMM", "Communication Sociale"),
        ("SOCIO", "Sociologie"),
        ("TS", "Travail Social"),
    ]

    # Icônes et couleurs pour le JS/CSS
    CHOIX_COULEUR = [
        ("primary", "Bleu (primary)"),
        ("secondary", "Violet (secondary)"),
        ("success", "Vert (success)"),
        ("accent", "Jaune (accent)"),
    ]

    code = models.CharField(
        "Code", max_length=20, unique=True, choices=CHOIX_DEPARTEMENT
    )
    slug = models.SlugField(
        "Slug",
        max_length=50,
        unique=True,
        help_text="Ex: psychologie, sociologie — utilisé dans les URLs et le JS",
    )
    nom = models.CharField("Nom du département", max_length=100, unique=True)
    description = models.TextField("Description courte (hero)", blank=True)
    couleur = models.CharField(
        "Couleur CSS", max_length=20, choices=CHOIX_COULEUR, default="primary"
    )
    emoji = models.CharField(
        "Emoji",
        max_length=10,
        default="🎓",
        help_text="Affiché dans le bouton de navigation hero",
    )
    slogan = models.CharField(
        "Slogan court", max_length=100, blank=True, help_text="Ex: Comprendre l'esprit"
    )

    # Image hero (optionnelle, sinon on garde les URLs Unsplash en fallback)
    image_hero = models.ImageField(
        "Image hero", upload_to="departements/hero/", null=True, blank=True
    )
    image_hero_url = models.URLField(
        "URL image hero (externe)",
        blank=True,
        help_text="URL Unsplash ou autre si pas d'upload",
    )

    # Statistiques clés (sidebar)
    nb_etudiants_affiche = models.CharField(
        "Étudiants actifs (affiché)", max_length=20, default="—"
    )
    taux_reussite = models.CharField(
        "Taux de réussite (affiché)", max_length=10, default="—"
    )
    taux_insertion = models.CharField(
        "Taux insertion pro (affiché)", max_length=10, default="—"
    )

    # Date limite inscription
    date_limite_inscription = models.DateField(
        "Date limite inscription", null=True, blank=True
    )

    # Conditions d'admission (texte libre, une par ligne)
    conditions_admission = models.TextField(
        "Conditions d'admission", blank=True, help_text="Une condition par ligne"
    )

    # Domaines d'expertise / spécialités (badges), séparés par virgule
    specialites = models.TextField(
        "Spécialités (séparées par virgule)",
        blank=True,
        help_text="Ex: Psychologie Clinique, Psychologie Sociale",
    )

    est_actif = models.BooleanField("Actif", default=True)
    ordre = models.PositiveSmallIntegerField("Ordre d'affichage", default=0)

    chef_departement = models.ForeignKey(
        "comptes.Professeur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departement_dirige",
        verbose_name="Chef de département",
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom

    def get_image_hero(self):
        """Retourne l'URL de l'image hero (upload prioritaire, sinon URL externe)."""
        if self.image_hero:
            return self.image_hero.url
        return self.image_hero_url or ""

    def get_specialites_liste(self):
        """Retourne les spécialités sous forme de liste Python."""
        return [s.strip() for s in self.specialites.split(",") if s.strip()]

    def get_conditions_liste(self):
        """Retourne les conditions d'admission sous forme de liste."""
        return [c.strip() for c in self.conditions_admission.splitlines() if c.strip()]

    def obtenir_total_etudiants(self):
        return self.etudiants.filter(utilisateur__is_active=True).count()

    def obtenir_total_professeurs(self):
        return self.professeurs.filter(utilisateur__is_active=True).count()

    @property
    def professeurs_actifs(self):
        """Professeurs actifs du département, pour l'affichage public"""
        return self.professeurs.filter(utilisateur__is_active=True)
