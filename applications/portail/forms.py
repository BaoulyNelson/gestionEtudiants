import datetime

from django import forms
from .models import Emprunt, Examen, Reservation, SiteSettings
from applications.cours.models import SectionCours


class FormulaireParametresSite(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "nom_etablissement", "nom_complet", "slogan", "annee_fondation",
            "adresse_ligne1", "telephone", "email",
            "logo", "logo_small",
            "nom_directeur_etudes", "titre_directeur_etudes",
            "signature_directeur", "cachet_officiel",
            "lien_twitter", "lien_facebook", "lien_linkedin",
            "annee_copyright",
        ]
        widgets = {
            "nom_etablissement":      forms.TextInput(attrs={"class": "form-control"}),
            "nom_complet":            forms.TextInput(attrs={"class": "form-control"}),
            "slogan":                 forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "annee_fondation":        forms.NumberInput(attrs={"class": "form-control"}),
            "adresse_ligne1":         forms.TextInput(attrs={"class": "form-control"}),
            "telephone":              forms.TextInput(attrs={"class": "form-control"}),
            "email":                  forms.EmailInput(attrs={"class": "form-control"}),
            "nom_directeur_etudes":   forms.TextInput(attrs={"class": "form-control"}),
            "titre_directeur_etudes": forms.TextInput(attrs={"class": "form-control"}),
            "logo":                   forms.FileInput(attrs={"class": "form-control"}),
            "logo_small":             forms.FileInput(attrs={"class": "form-control"}),
            "signature_directeur":    forms.FileInput(attrs={"class": "form-control"}),
            "cachet_officiel":        forms.FileInput(attrs={"class": "form-control"}),
            "lien_twitter":           forms.URLInput(attrs={"class": "form-control"}),
            "lien_facebook":          forms.URLInput(attrs={"class": "form-control"}),
            "lien_linkedin":          forms.URLInput(attrs={"class": "form-control"}),
            "annee_copyright":        forms.NumberInput(attrs={"class": "form-control"}),
        }


class ExamenForm(forms.ModelForm):
    """
    Formulaire de création/modification d'un examen.
    Le queryset de section_cours est filtré selon le rôle :
    - Admin/superuser : toutes les sections
    - Professeur      : ses sections uniquement
    """

    class Meta:
        model  = Examen
        fields = ['section_cours', 'type_examen', 'date', 'heure', 'salle', 'duree_minutes', 'description']
        # statut est exclu : recalculé automatiquement par Examen.save()

        widgets = {
            'section_cours': forms.Select(attrs={
                'class': 'form-select',
            }),
            'type_examen': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',
            }),
            'heure': forms.TimeInput(attrs={
                'class': 'form-control',
                'type':  'time',
            }),
            'salle': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Ex : Salle A-101',
            }),
            'duree_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   '15',
                'step':  '15',
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': 'Instructions, documents autorisés, chapitres couverts…',
            }),
        }

        labels = {
            'section_cours':  'Section de cours',
            'type_examen':    "Type d'examen",
            'date':           "Date",
            'heure':          "Heure de début",
            'salle':          "Salle",
            'duree_minutes':  "Durée (minutes)",
            'description':    "Remarques / Instructions",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Filtrage du queryset selon le rôle
        if user is not None and not user.is_superuser and not user.est_administrateur():
            if user.est_professeur():
                self.fields['section_cours'].queryset = (
                    user.profil_professeur.sections_cours
                    .select_related('cours', 'cours__departement')
                    .order_by('cours__code', 'numero_section')
                )
            else:
                self.fields['section_cours'].queryset = SectionCours.objects.none()
        else:
            self.fields['section_cours'].queryset = (
                SectionCours.objects
                .select_related('cours', 'cours__departement', 'professeur__utilisateur')
                .order_by('cours__departement__nom', 'cours__code', 'numero_section')
            )

        # Libellé lisible pour chaque section
        self.fields['section_cours'].label_from_instance = lambda s: (
            f"{s.cours.code} — {s.cours.nom} "
            f"| Section {s.numero_section} "
            f"| {s.get_semestre_display()} {s.annee}"
        )
        
        
from django import forms
from .models import Personnel, Livre


class FormulairePersonnel(forms.ModelForm):
    class Meta:
        model = Personnel
        fields = ["poste", "departement", "nom", "description", "photo"]
        widgets = {
            "poste":        forms.Select(attrs={"class": "form-select", "id": "id_poste"}),
            "departement":  forms.Select(attrs={"class": "form-select", "id": "id_departement"}),
            "nom":          forms.TextInput(attrs={"class": "form-control"}),
            "description":  forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "photo":        forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # departement n'est pas obligatoire au niveau du form —
        # la validation métier est dans Personnel.clean()
        self.fields["departement"].required = False
        self.fields["departement"].empty_label = "— Sélectionner un département —"
        self.fields["photo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        # Déclenche le clean() du modèle pour valider la règle chef_dept ↔ departement
        instance = self.instance
        for field, value in cleaned_data.items():
            setattr(instance, field, value)
        try:
            instance.clean()
        except forms.ValidationError as e:
            self._update_errors(e)
        return cleaned_data


class FormulaireLivre(forms.ModelForm):
    class Meta:
        model  = Livre
        fields = [
            "titre",
            "auteur",
            "isbn",
            "editeur",
            "annee",
            "categorie",
            "resume",
            "couverture",
            "nombre_exemplaires",
        ]
        widgets = {
            "titre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Titre du livre",
            }),
            "auteur": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nom de l'auteur",
            }),
            "isbn": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "978-...",
            }),
            "editeur": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nom de l'éditeur",
            }),
            "annee": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": datetime.date.today().year,
            }),
            "categorie": forms.Select(attrs={
                "class": "form-select",
            }),
            "resume": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Résumé du livre...",
            }),
            "couverture": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
            "nombre_exemplaires": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
            }),
        }
        labels = {
            "titre":              "Titre",
            "auteur":             "Auteur(s)",
            "isbn":               "ISBN",
            "editeur":            "Éditeur",
            "annee":              "Année de publication",
            "categorie":          "Catégorie",
            "resume":             "Résumé",
            "couverture":         "Image de couverture",
            "nombre_exemplaires": "Nombre d'exemplaires",
        }
        help_texts = {
            "isbn":               "Optionnel — doit être unique si renseigné.",
            "nombre_exemplaires": "Nombre total d'exemplaires en médiathèque.",
            "couverture":         "Formats acceptés : JPG, PNG, WebP.",
        }

    def clean_annee(self):
        annee = self.cleaned_data.get("annee")
        if annee and annee > datetime.date.today().year:
            raise forms.ValidationError("L'année ne peut pas être dans le futur.")
        if annee and annee < 1:
            raise forms.ValidationError("L'année doit être un nombre positif.")
        return annee

    def clean_nombre_exemplaires(self):
        n = self.cleaned_data.get("nombre_exemplaires")
        if n is not None and n < 1:
            raise forms.ValidationError("Il doit y avoir au moins un exemplaire.")
        return n

    def clean_isbn(self):
        isbn = self.cleaned_data.get("isbn")
        if not isbn:
            return isbn  # champ optionnel
        isbn_clean = isbn.replace("-", "").replace(" ", "")
        if len(isbn_clean) not in (10, 13) or not isbn_clean.isdigit():
            raise forms.ValidationError("ISBN invalide : 10 ou 13 chiffres attendus.")
        return isbn_clean
    
    
class FormulaireEmprunt(forms.ModelForm):
    class Meta:
        model  = Emprunt
        fields = [
            "utilisateur",
            "livre",
            "date_emprunt",
            "date_retour_prevue",
            "note_admin",
        ]
        # statut, date_retour_effective → gérés par les vues/actions dédiées
        widgets = {
            "utilisateur": forms.Select(attrs={
                "class": "form-select",
            }),
            "livre": forms.Select(attrs={
                "class": "form-select",
            }),
            "date_emprunt": forms.DateInput(attrs={
                "class": "form-control",
                "type":  "date",
            }),
            "date_retour_prevue": forms.DateInput(attrs={
                "class": "form-control",
                "type":  "date",
            }),
            "note_admin": forms.Textarea(attrs={
                "class":       "form-control",
                "rows":        3,
                "placeholder": "Note interne (facultatif)...",
            }),
        }
        labels = {
            "utilisateur":      "Emprunteur",
            "livre":            "Livre emprunté",
            "date_emprunt":     "Date d'emprunt",
            "date_retour_prevue": "Date de retour prévue",
            "note_admin":       "Note interne",
        }
        help_texts = {
            "date_retour_prevue": f"Par défaut : {Emprunt.DUREE_DEFAUT_JOURS} jours après l'emprunt.",
            "note_admin":         "Visible uniquement par les administrateurs.",
        }

    def clean(self):
        cleaned_data       = super().clean()
        date_emprunt       = cleaned_data.get("date_emprunt")
        date_retour_prevue = cleaned_data.get("date_retour_prevue")
        livre              = cleaned_data.get("livre")

        # La date de retour doit être après la date d'emprunt
        if date_emprunt and date_retour_prevue:
            if date_retour_prevue <= date_emprunt:
                raise forms.ValidationError(
                    "La date de retour prévue doit être postérieure à la date d'emprunt."
                )

        # Vérifier qu'il reste un exemplaire disponible
        if livre and not livre.disponible:
            raise forms.ValidationError(
                f"« {livre.titre} » n'a plus d'exemplaire disponible."
            )

        return cleaned_data
    
class FormulaireRetour(forms.ModelForm):
    class Meta:
        model  = Emprunt
        fields = ["date_retour_effective", "note_admin"]
        widgets = {
            "date_retour_effective": forms.DateInput(attrs={
                "class": "form-control",
                "type":  "date",
            }),
            "note_admin": forms.Textarea(attrs={
                "class": "form-control",
                "rows":  2,
            }),
        }
        labels = {
            "date_retour_effective": "Date de retour effective",
            "note_admin":            "Note interne",
        }

    def clean_date_retour_effective(self):
        date = self.cleaned_data.get("date_retour_effective")
        if date and date > datetime.date.today():
            raise forms.ValidationError("La date de retour ne peut pas être dans le futur.")
        return date

    def save(self, commit=True):
        emprunt = super().save(commit=False)
        emprunt.statut = "rendu"
        if commit:
            emprunt.save()
        return emprunt
    
class FormulaireReservation(forms.ModelForm):
    class Meta:
        model  = Reservation
        fields = ["utilisateur", "livre"]
        # statut et date_disponibilite → gérés par notifier_disponible()
        widgets = {
            "utilisateur": forms.Select(attrs={
                "class": "form-select",
            }),
            "livre": forms.Select(attrs={
                "class": "form-select",
            }),
        }
        labels = {
            "utilisateur": "Utilisateur",
            "livre":       "Livre à réserver",
        }

    def clean(self):
        cleaned_data = super().clean()
        utilisateur  = cleaned_data.get("utilisateur")
        livre        = cleaned_data.get("livre")

        if utilisateur and livre:
            # Doublon : réservation déjà active pour ce couple
            deja_reserve = Reservation.objects.filter(
                utilisateur=utilisateur,
                livre=livre,
                statut__in=["en_attente", "disponible"],
            ).exists()
            if deja_reserve:
                raise forms.ValidationError(
                    f"« {utilisateur.get_full_name()} » a déjà une réservation active pour ce livre."
                )

            # Inutile de réserver si le livre est disponible
            if livre.disponible:
                raise forms.ValidationError(
                    f"« {livre.titre} » est disponible — un emprunt direct est possible."
                )

        return cleaned_data