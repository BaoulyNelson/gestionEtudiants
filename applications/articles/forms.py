from django import forms
from .models import Publication, MetriqueRecherche, Partenariat


class FormulairePublication(forms.ModelForm):
    """Formulaire de création/édition d'une publication (vedette ou archive)."""

    class Meta:
        model = Publication
        fields = [
            'titre', 'type_publication', 'statut', 'langue', 'departement',
            'resume', 'contenu',
            'auteurs_texte', 'auteur_principal', 'auteur_etudiant',
            'revue', 'annee_publication', 'date_publication', 'periode_projet',
            'image', 'fichier_pdf',
            'est_vedette', 'est_actif',
        ]
        # NB : le slug n'est pas exposé (généré automatiquement dans save()),
        # de même que nombre_vues / nombre_citations / cree_le / modifie_le.
        widgets = {
            'resume': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'auteurs_texte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Jean-Claude Moïse, Marie Dupont',
            }),
            'periode_projet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : 2023-2025',
            }),
            'revue': forms.TextInput(attrs={'class': 'form-control'}),
            'date_publication': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'annee_publication': forms.NumberInput(attrs={'class': 'form-control'}),
            'type_publication': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'langue': forms.Select(attrs={'class': 'form-select'}),
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'auteur_principal': forms.Select(attrs={'class': 'form-select'}),
            'auteur_etudiant': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        donnees_nettoyees = super().clean()
        annee = donnees_nettoyees.get('annee_publication')
        date_pub = donnees_nettoyees.get('date_publication')

        # Cohérence entre l'année déclarée et la date précise (si les deux sont fournies)
        if date_pub and annee and date_pub.year != annee:
            self.add_error(
                'annee_publication',
                "L'année de publication doit correspondre à l'année de la date de publication."
            )

        return donnees_nettoyees


class FormulaireMetriqueRecherche(forms.ModelForm):
    """Formulaire pour les chiffres d'impact (section « Impact de Notre Recherche »)."""

    class Meta:
        model = MetriqueRecherche
        fields = ['valeur', 'libelle', 'couleur', 'icone', 'ordre', 'est_actif']
        widgets = {
            'valeur': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : 847 ou 2 341',
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : Publications Totales',
            }),
            'couleur': forms.Select(attrs={'class': 'form-select'}),
            'icone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ex : bi-book, bi-journal-text',
            }),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class FormulairePartenariat(forms.ModelForm):
    """Formulaire pour les partenariats (section « Opportunités de Collaboration »)."""

    class Meta:
        model = Partenariat
        fields = ['nom', 'categorie', 'ordre', 'est_actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }