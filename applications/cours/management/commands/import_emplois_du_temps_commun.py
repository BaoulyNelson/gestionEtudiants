"""
Commande d'import spéciale pour emploi_du_temps_commun.csv.

Contrairement aux fichiers par département (où le département et le niveau
sont déduits du nom du fichier), le fichier commun contient des cours de
plusieurs départements et niveaux mélangés. Le département et le niveau sont
donc lus directement depuis les colonnes « departement » et « niveau » du CSV.

Usage :
    python manage.py import_emplois_du_temps_commun donnees/emploi_du_temps_commun.csv --annee 2026 --semestre PRINTEMPS --dry-run
    python manage.py import_emplois_du_temps_commun donnees/emploi_du_temps_commun.csv --annee 2026 --semestre PRINTEMPS
"""

import csv
import os

from .import_emplois_du_temps import Command as BaseImportCommand


# Correspondance nom complet (colonne CSV) -> code court Django
DEPT_NOM_VERS_CODE = {
    "Sociologie":           "SOCIO",
    "Communication Sociale": "COMM",
    "Travail Social":       "TS",
    "Psychologie":          "PSY",
    "Préparatoire":         None,
}

# Correspondance libellé niveau (colonne CSV) -> constante Django
NIVEAU_LABEL_VERS_CODE = {
    "Niveau I":   "NIVEAU1",
    "Niveau II":  "NIVEAU2",
    "Niveau III": "NIVEAU3",
    "Préparatoire": "PREPARATOIRE",
}


class Command(BaseImportCommand):
    help = "Importe emploi_du_temps_commun.csv (cours multi-départements / multi-niveaux)."

    def _deduire_departement_niveau(self, nom_fichier):
        """
        Pour le fichier commun on ne peut pas déduire un seul département/niveau
        depuis le nom — on retourne des sentinelles (None, None) et on laisse
        _traiter_ligne lire les colonnes CSV ligne par ligne.
        """
        if nom_fichier == "emploi_du_temps_commun.csv":
            return None, None          # sentinelles : sera résolu par ligne
        return super()._deduire_departement_niveau(nom_fichier)

    def _traiter_ligne(self, ligne, num_ligne, nom_fichier,
                       departement_attendu, niveau_attendu, options):
        """
        Surcharge : si département/niveau sont None (fichier commun), on les
        résout depuis les colonnes CSV avant de déléguer au parent.
        """
        if departement_attendu is None and niveau_attendu is None:
            # Lire les colonnes du CSV
            dept_csv   = (ligne.get("departement") or "").strip()
            niveau_csv = (ligne.get("niveau") or "").strip()

            if dept_csv not in DEPT_NOM_VERS_CODE:
                self.stdout.write(self.style.WARNING(
                    f"  Ligne {num_ligne} : département CSV inconnu « {dept_csv} », ignorée."
                ))
                self._stats["ignorees_format"] += 1
                return

            if niveau_csv not in NIVEAU_LABEL_VERS_CODE:
                self.stdout.write(self.style.WARNING(
                    f"  Ligne {num_ligne} : niveau CSV inconnu « {niveau_csv} », ignorée."
                ))
                self._stats["ignorees_format"] += 1
                return

            code_dept  = DEPT_NOM_VERS_CODE[dept_csv]
            code_niveau = NIVEAU_LABEL_VERS_CODE[niveau_csv]

            departement_attendu = self._obtenir_departement(code_dept)
            niveau_attendu      = code_niveau

        super()._traiter_ligne(
            ligne, num_ligne, nom_fichier,
            departement_attendu, niveau_attendu, options,
        )