from django import forms
from django.utils import timezone
from django.utils.text import slugify
from .models import Annonce, Article, Categorie, Evenement, Tag

_INPUT = "form-control"
_SELECT = "form-select"


class FormulaireArticle(forms.ModelForm):
    tags_input = forms.CharField(
        label="Tags",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": _INPUT,
                "placeholder": "politique, economie, culture  (virgules)",
                "id": "tags-input",
            }
        ),
        help_text="Tags separes par des virgules",
    )

    class Meta:
        model = Article
        fields = [
            "titre",
            "categorie",
            "extrait",
            "contenu",
            "image_principale",
            "statut",
            "est_a_la_une",
            "est_breaking",
        ]
        widgets = {
            "titre": forms.TextInput(
                attrs={
                    "class": _INPUT + " form-control-lg",
                    "placeholder": "Titre de l'article",
                }
            ),
            "categorie": forms.Select(attrs={"class": _SELECT}),
            "extrait": forms.Textarea(
                attrs={
                    "class": _INPUT,
                    "rows": 3,
                    "placeholder": "Resume court (genere automatiquement si vide)",
                }
            ),
            "contenu": forms.Textarea(
                attrs={"class": _INPUT, "id": "article-content", "rows": 20}
            ),
            "image_principale": forms.FileInput(attrs={"class": _INPUT}),
            "statut": forms.Select(attrs={"class": _SELECT}),
            "est_a_la_une": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "est_breaking": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "titre": "Titre *",
            "categorie": "Categorie",
            "extrait": "Extrait / Resume",
            "contenu": "Contenu *",
            "image_principale": "Image principale",
            "statut": "Statut",
            "est_a_la_une": "Mettre a la une",
            "est_breaking": "Breaking news",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tags_input"].initial = ", ".join(
                t.nom for t in self.instance.tags.all()
            )

    def save(self, commit=True):
        article = super().save(commit=False)
        if self.user and not article.auteur_id:
            article.auteur = self.user
        if article.statut == "publie" and not article.publie_le:
            article.publie_le = timezone.now()
        if commit:
            article.save()
            article.tags.clear()
            raw = self.cleaned_data.get("tags_input", "")
            for name in [t.strip() for t in raw.split(",") if t.strip()]:
                tag, _ = Tag.objects.get_or_create(
                    slug=slugify(name), defaults={"nom": name}
                )
                article.tags.add(tag)
        return article


class FormulaireCategorieAdmin(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ["nom", "description", "image", "couleur", "ordre"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(
                attrs={"class": "form-control", "type": "color"}
            ),
            "ordre": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "nom": "Nom de la categorie",
            "description": "Description",
            "image": "Image",
            "couleur": "Couleur d'accentuation",
            "ordre": "Ordre d'affichage",
        }


from django import forms
from .models import Publication, MetriqueRecherche, Partenariat


class FormulairePublication(forms.ModelForm):
    """Formulaire de création/édition d'une publication (vedette ou archive)."""

    class Meta:
        model = Publication
        fields = [
            "titre",
            "type_publication",
            "statut",
            "langue",
            "departement",
            "resume",
            "contenu",
            "auteurs_texte",
            "auteur_principal",
            "auteur_etudiant",
            "revue",
            "annee_publication",
            "date_publication",
            "periode_projet",
            "image",
            "fichier_pdf",
            "est_vedette",
            "est_actif",
        ]
        # NB : le slug n'est pas exposé (généré automatiquement dans save()),
        # de même que nombre_vues / nombre_citations / cree_le / modifie_le.
        widgets = {
            "resume": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "contenu": forms.Textarea(attrs={"rows": 10, "class": "form-control"}),
            "auteurs_texte": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : Jean-Claude Moïse, Marie Dupont",
                }
            ),
            "periode_projet": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : 2023-2025",
                }
            ),
            "revue": forms.TextInput(attrs={"class": "form-control"}),
            "date_publication": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "annee_publication": forms.NumberInput(attrs={"class": "form-control"}),
            "type_publication": forms.Select(attrs={"class": "form-select"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
            "langue": forms.Select(attrs={"class": "form-select"}),
            "departement": forms.Select(attrs={"class": "form-select"}),
            "auteur_principal": forms.Select(attrs={"class": "form-select"}),
            "auteur_etudiant": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        donnees_nettoyees = super().clean()
        annee = donnees_nettoyees.get("annee_publication")
        date_pub = donnees_nettoyees.get("date_publication")

        # Cohérence entre l'année déclarée et la date précise (si les deux sont fournies)
        if date_pub and annee and date_pub.year != annee:
            self.add_error(
                "annee_publication",
                "L'année de publication doit correspondre à l'année de la date de publication.",
            )

        return donnees_nettoyees


class FormulaireMetriqueRecherche(forms.ModelForm):
    """Formulaire pour les chiffres d'impact (section « Impact de Notre Recherche »)."""

    class Meta:
        model = MetriqueRecherche
        fields = ["valeur", "libelle", "couleur", "icone", "ordre", "est_actif"]
        widgets = {
            "valeur": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : 847 ou 2 341",
                }
            ),
            "libelle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : Publications Totales",
                }
            ),
            "couleur": forms.Select(attrs={"class": "form-select"}),
            "icone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : bi-book, bi-journal-text",
                }
            ),
            "ordre": forms.NumberInput(attrs={"class": "form-control"}),
        }


class FormulairePartenariat(forms.ModelForm):
    """Formulaire pour les partenariats (section « Opportunités de Collaboration »)."""

    class Meta:
        model = Partenariat
        fields = ["nom", "categorie", "ordre", "est_actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control"}),
        }






class FormulaireEvenement(forms.ModelForm):
    """Formulaire de création/édition d'un événement."""

    class Meta:
        model = Evenement
        fields = [
            "titre",
            "description",
            "date_debut",
            "date_fin",
            "lieu",
            "image",
        ]
        # NB : le slug n'est pas exposé (généré automatiquement dans save()),
        # de même que date_creation (editable=False).
        widgets = {
            "titre": forms.TextInput(
                attrs={"class": _INPUT, "placeholder": "Titre de l'événement"}
            ),
            "description": forms.Textarea(
                attrs={"class": _INPUT, "rows": 5}
            ),
            "date_debut": forms.DateTimeInput(
                attrs={"class": _INPUT, "type": "datetime-local"}
            ),
            "date_fin": forms.DateTimeInput(
                attrs={"class": _INPUT, "type": "datetime-local"}
            ),
            "lieu": forms.TextInput(
                attrs={"class": _INPUT, "placeholder": "Ex : Amphithéâtre A"}
            ),
            "image": forms.FileInput(attrs={"class": _INPUT}),
        }
        labels = {
            "titre": "Titre *",
            "description": "Description *",
            "date_debut": "Date et heure de début *",
            "date_fin": "Date et heure de fin *",
            "lieu": "Lieu",
            "image": "Image",
        }

    def clean(self):
        donnees_nettoyees = super().clean()
        date_debut = donnees_nettoyees.get("date_debut")
        date_fin = donnees_nettoyees.get("date_fin")

        if date_debut and date_fin and date_fin <= date_debut:
            self.add_error(
                "date_fin",
                "La date de fin doit être postérieure à la date de début.",
            )

        return donnees_nettoyees


class FormulaireAnnonce(forms.ModelForm):
    """Formulaire de création/édition d'une annonce."""

    class Meta:
        model = Annonce
        fields = [
            "titre",
            "contenu",
            "organisateur",
            "lieu",
            "date_evenement",
            "image",
            "est_active",
        ]
        # NB : le slug n'est pas exposé (généré automatiquement dans save()),
        # de même que date_publication (auto_now_add).
        widgets = {
            "titre": forms.TextInput(
                attrs={"class": _INPUT, "placeholder": "Titre de l'annonce"}
            ),
            "contenu": forms.Textarea(
                attrs={"class": _INPUT, "rows": 5}
            ),
            "organisateur": forms.TextInput(attrs={"class": _INPUT}),
            "lieu": forms.TextInput(
                attrs={"class": _INPUT, "placeholder": "Ex : Salle de conférence"}
            ),
            "date_evenement": forms.DateTimeInput(
                attrs={"class": _INPUT, "type": "datetime-local"}
            ),
            "image": forms.FileInput(attrs={"class": _INPUT}),
            "est_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "titre": "Titre *",
            "contenu": "Contenu *",
            "organisateur": "Organisateur",
            "lieu": "Lieu",
            "date_evenement": "Date de l'événement (le cas échéant)",
            "image": "Image",
            "est_active": "Annonce active",
        }