# forms.py

from django import forms
from .models import (
    Candidature,
    Statistique,
    Ambassadeur,
    FAQ,
    TypeBourse,
    VisiteVirtuelle,
)
from applications.departements.models import Departement

# ─────────────────────────────────────────
# CANDIDATURE
# ─────────────────────────────────────────


class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = [
            "prenom",
            "nom",
            "email",
            "telephone",
            "programme",
            "lettre_motivation",
            "accepte_conditions",
        ]
        widgets = {
            "prenom": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Votre prénom"}
            ),
            "nom": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Votre nom de famille"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "exemple@email.com"}
            ),
            "telephone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+509XXXXXXXX"}
            ),
            "programme": forms.Select(attrs={"class": "form-select"}),
            "lettre_motivation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": "Expliquez vos motivations, votre parcours et vos objectifs...",
                }
            ),
            "accepte_conditions": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_lettre_motivation(self):
        lettre = self.cleaned_data.get("lettre_motivation", "")
        if len(lettre.split()) < 50:
            raise forms.ValidationError(
                "La lettre de motivation doit contenir au moins 50 mots."
            )
        return lettre

    def clean_accepte_conditions(self):
        accepte = self.cleaned_data.get("accepte_conditions")
        if not accepte:
            raise forms.ValidationError(
                "Vous devez accepter les conditions pour soumettre votre candidature."
            )
        return accepte

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        # Bloque les domaines jetables courants
        domaines_bloques = ["tempmail.com", "mailinator.com", "guerrillamail.com"]
        domaine = email.split("@")[-1] if "@" in email else ""
        if domaine in domaines_bloques:
            raise forms.ValidationError(
                "Veuillez utiliser une adresse email valide et permanente."
            )
        return email


class CandidatureStatutForm(forms.ModelForm):
    """Réservé aux administrateurs pour changer le statut d'une candidature."""

    class Meta:
        model = Candidature
        fields = ["statut"]
        widgets = {
            "statut": forms.Select(attrs={"class": "form-select"}),
        }


# ─────────────────────────────────────────
# STATISTIQUE
# ─────────────────────────────────────────


class StatistiqueForm(forms.ModelForm):
    class Meta:
        model = Statistique
        fields = ["valeur", "label", "couleur", "ordre", "actif"]
        widgets = {
            "valeur": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: 94%, 2 847, 85%"}
            ),
            "label": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: Taux d'Acceptation"}
            ),
            "couleur": forms.Select(attrs={"class": "form-select"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_valeur(self):
        valeur = self.cleaned_data.get("valeur", "").strip()
        if not valeur:
            raise forms.ValidationError("La valeur ne peut pas être vide.")
        return valeur


# ─────────────────────────────────────────
# AMBASSADEUR
# ─────────────────────────────────────────


class AmbassadeurForm(forms.ModelForm):
    # Champ texte pour saisir les spécialités séparées par virgule
    specialites_input = forms.CharField(
        label="Spécialités",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex: Psychologie clinique, Recherche, Linguistique",
            }
        ),
        help_text="Séparez les spécialités par des virgules.",
    )

    class Meta:
        model = Ambassadeur
        fields = [
            "nom",
            "photo",
            "programme",
            "annee",
            "temoignage",
            "email",
            "ordre",
            "actif",
        ]
        widgets = {
            "nom": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nom complet"}
            ),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "programme": forms.Select(attrs={"class": "form-select"}),
            "annee": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: 3ème année"}
            ),
            "temoignage": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Citation courte de l'ambassadeur...",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "email@exemple.com"}
            ),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir le champ texte depuis le JSONField existant
        if self.instance.pk and self.instance.specialites:
            self.fields["specialites_input"].initial = ", ".join(
                self.instance.specialites
            )

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and hasattr(photo, "size"):
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("La photo ne doit pas dépasser 2 Mo.")
            import os

            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                raise forms.ValidationError("Formats acceptés : JPG, PNG, WEBP.")
        return photo

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data.get("specialites_input", "")
        instance.specialites = [s.strip() for s in raw.split(",") if s.strip()]
        if commit:
            instance.save()
        return instance


# ─────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ["question", "reponse", "categorie", "ordre", "actif"]
        widgets = {
            "question": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "La question telle qu'elle sera affichée",
                }
            ),
            "reponse": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Réponse claire et concise...",
                }
            ),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_question(self):
        question = self.cleaned_data.get("question", "").strip()
        if not question.endswith("?"):
            question += "?"
        return question

    def clean_reponse(self):
        reponse = self.cleaned_data.get("reponse", "").strip()
        if len(reponse) < 10:
            raise forms.ValidationError("La réponse est trop courte.")
        return reponse


# ─────────────────────────────────────────
# TYPE DE BOURSE
# ─────────────────────────────────────────


class TypeBourseForm(forms.ModelForm):
    # Champ texte pour les critères (JSONField → input lisible)
    criteres_input = forms.CharField(
        label="Critères d'éligibilité",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Un critère par ligne.\nEx:\nMoyenne ≥ 15/20\nDossier complet\nRésidence en Haïti",
            }
        ),
        help_text="Saisissez un critère par ligne.",
    )

    class Meta:
        model = TypeBourse
        fields = [
            "nom",
            "description",
            "pourcentage",
            "nombre_disponible",
            "couleur",
            "icone_svg",
            "actif",
            "ordre",
        ]
        widgets = {
            "nom": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Bourse d'Excellence Académique",
                }
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "pourcentage": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 100}
            ),
            "nombre_disponible": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "couleur": forms.Select(attrs={"class": "form-select"}),
            "icone_svg": forms.Textarea(
                attrs={
                    "class": "form-control font-monospace",
                    "rows": 5,
                    "placeholder": '<svg xmlns="http://www.w3.org/2000/svg" ...>...</svg>',
                }
            ),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.criteres:
            self.fields["criteres_input"].initial = "\n".join(self.instance.criteres)

    def clean_icone_svg(self):
        svg = self.cleaned_data.get("icone_svg", "").strip()
        if svg and not svg.startswith("<svg"):
            raise forms.ValidationError(
                "Le code doit être un SVG valide commençant par <svg."
            )
        return svg

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data.get("criteres_input", "")
        instance.criteres = [
            ligne.strip() for ligne in raw.splitlines() if ligne.strip()
        ]
        if commit:
            instance.save()
        return instance


# ─────────────────────────────────────────
# VISITE VIRTUELLE
# ─────────────────────────────────────────


class VisiteVirtuelleForm(forms.ModelForm):
    class Meta:
        model = VisiteVirtuelle
        fields = [
            "titre",
            "sous_titre",
            "description",
            "image",
            "url_visite",
            "couleur",
            "actif",
            "ordre",
        ]
        widgets = {
            "titre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Bibliothèque Centrale",
                }
            ),
            "sous_titre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: 50 000 ouvrages spécialisés",
                }
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "url_visite": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://..."}
            ),
            "couleur": forms.Select(attrs={"class": "form-select"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "size"):
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("L'image ne doit pas dépasser 5 Mo.")
            import os

            ext = os.path.splitext(image.name)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                raise forms.ValidationError("Formats acceptés : JPG, PNG, WEBP.")
        return image

    def clean_url_visite(self):
        url = self.cleaned_data.get("url_visite", "")
        if url and not url.startswith("https://"):
            raise forms.ValidationError("L'URL doit commencer par https://")
        return url
