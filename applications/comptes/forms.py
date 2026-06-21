from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Utilisateur, Etudiant, Professeur, Administrateur


class FormulaireConnexion(forms.Form):
    """Formulaire de connexion"""

    identifiant = forms.CharField(
        label="Identifiant",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email, téléphone ou numéro étudiant",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "motdepasse123"}
        ),
    )


class FormulaireChangementMotDePasse(PasswordChangeForm):
    """Formulaire de changement de mot de passe"""

    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Ancien mot de passe"}
        ),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Nouveau mot de passe"}
        ),
        help_text="Minimum 8 caractères",
    )
    new_password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirmer le mot de passe"}
        ),
    )


class FormulaireUtilisateur(forms.ModelForm):
    """Formulaire unique pour la création ET la modification d'un utilisateur.
    En mode création (pas d'instance) : le champ `role` est présent.
    En mode modification (instance existante) : `role` est masqué et verrouillé.
    """

    class Meta:
        model = Utilisateur
        fields = [
            "email",
            "first_name",
            "last_name",
            "role",
            "role_editorial",
            "genre",
            "numero_telephone",
            "adresse",
            "date_naissance",
            "photo_profil",
            "is_active",
        ]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "role_editorial": forms.Select(attrs={"class": "form-select"}),
            "genre": forms.Select(attrs={"class": "form-select"}),
            "numero_telephone": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "date_naissance": forms.DateInput(
            attrs={"class": "form-control", "type": "date"},
            format="%Y-%m-%d",
        ),
            "photo_profil": forms.FileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Mode modification : le rôle ne peut pas changer
            self.fields["role"].disabled = True
            self.fields["role"].help_text = (
                "Le rôle ne peut pas être modifié après la création."
            )

    def clean_numero_telephone(self):
        valeur = self.cleaned_data.get("numero_telephone") or ""  # None → ''
        return valeur.strip() or None

class FormulaireProfilUtilisateur(forms.ModelForm):
    """Formulaire de modification du profil personnel (sans email ni rôle)."""

    class Meta:
        model = Utilisateur
        fields = [
            "genre",
            "numero_telephone",
            "adresse",
            "date_naissance",
            "photo_profil",
        ]
        widgets = {
            "genre": forms.Select(attrs={"class": "form-select"}),
            "numero_telephone": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.Textarea(attrs={"class": "form-control", "rows": 3}),

            "date_naissance": forms.DateInput(
            attrs={"class": "form-control", "type": "date"},
            format="%Y-%m-%d",
        ),
            "photo_profil": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_numero_telephone(self):
        valeur = self.cleaned_data.get("numero_telephone") or ""
        valeur = valeur.strip() or None

        if valeur:
            qs = Utilisateur.objects.filter(numero_telephone=valeur)
            # Exclure l'utilisateur courant pour ne pas se bloquer lui-même
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Ce numéro de téléphone est déjà utilisé par un autre compte."
                )

        return valeur
    
    
    
class FormulaireCreationEtudiant(forms.ModelForm):
    """Formulaire de création de profil étudiant"""

    class Meta:
        model = Etudiant
        fields = ["numero_etudiant", "departement", "niveau", "date_inscription"]
        widgets = {
            "numero_etudiant": forms.TextInput(attrs={"class": "form-control"}),
            "departement": forms.Select(attrs={"class": "form-select"}),
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "date_inscription": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class FormulaireModificationEtudiant(forms.ModelForm):
    """Formulaire admin pour modifier le profil étudiant complet"""

    first_name = forms.CharField(
        label="Prénom", max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        label="Nom", max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    genre = forms.ChoiceField(
        label="Genre", choices=Utilisateur.CHOIX_GENRE,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    numero_telephone = forms.CharField(
        label="Téléphone", required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    adresse = forms.CharField(
        label="Adresse", required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2})
    )
    date_naissance = forms.DateField(
        label="Date de naissance", required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
        )
    )
    is_active = forms.BooleanField(
        label="Compte actif", required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Etudiant
        fields = ["departement", "niveau", "date_inscription"]
        widgets = {
            "departement": forms.Select(attrs={"class": "form-select"}),
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "date_inscription": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            u = self.instance.utilisateur
            self.fields["first_name"].initial       = u.first_name
            self.fields["last_name"].initial        = u.last_name
            self.fields["email"].initial            = u.email
            self.fields["genre"].initial            = u.genre
            self.fields["numero_telephone"].initial = u.numero_telephone or ""
            self.fields["adresse"].initial          = u.adresse
            self.fields["date_naissance"].initial   = u.date_naissance
            self.fields["is_active"].initial        = u.is_active

    def save(self, commit=True):
        etudiant = super().save(commit=False)
        u = etudiant.utilisateur
        u.first_name       = self.cleaned_data["first_name"]
        u.last_name        = self.cleaned_data["last_name"]
        u.email            = self.cleaned_data["email"]
        u.genre            = self.cleaned_data["genre"]
        u.numero_telephone = self.cleaned_data.get("numero_telephone") or None
        u.adresse          = self.cleaned_data.get("adresse", "")
        u.date_naissance   = self.cleaned_data.get("date_naissance")
        u.is_active        = self.cleaned_data.get("is_active", True)
        if commit:
            u.save()
            etudiant.save()
        return etudiant

class FormulaireCreationProfesseur(forms.ModelForm):
    """Formulaire de création de profil professeur"""

    class Meta:
        model = Professeur
        fields = [
            "identifiant_professeur",
            "departement",
            "specialite",
            "date_embauche",
        ]
        widgets = {
            "identifiant_professeur": forms.TextInput(attrs={"class": "form-control"}),
            "departement": forms.Select(attrs={"class": "form-select"}),
            "specialite": forms.TextInput(attrs={"class": "form-control"}),
            "date_embauche": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class FormulaireModificationProfesseur(forms.ModelForm):
    """Formulaire de modification de profil professeur"""

    class Meta:
        model = Professeur
        fields = ["departement", "specialite"]
        widgets = {
            "departement": forms.Select(attrs={"class": "form-select"}),
            "specialite": forms.TextInput(attrs={"class": "form-control"}),
        }


class FormulaireCreationAdministrateur(forms.ModelForm):
    """Formulaire de création de profil administrateur"""

    class Meta:
        model = Administrateur
        fields = ["identifiant_administrateur", "poste"]
        widgets = {
            "identifiant_administrateur": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "poste": forms.TextInput(attrs={"class": "form-control"}),
        }


class FormulaireModificationAdministrateur(forms.ModelForm):
    """Formulaire de modification de profil administrateur

    NB : ce formulaire était importé dans views.py mais n'existait pas
    dans forms.py (ImportError). Ajouté ici - seul 'poste' est modifiable,
    'identifiant_administrateur' n'est pas censé changer après création.
    """

    class Meta:
        model = Administrateur
        fields = ["poste"]
        widgets = {
            "poste": forms.TextInput(attrs={"class": "form-control"}),
        }