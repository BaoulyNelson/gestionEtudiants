"""
Commande d'import des cours depuis un fichier CSV.

Format CSV attendu (en-tête obligatoire) :
    departement,niveau,code,cours,credits,optionnel

Emplacement attendu : cours/management/commands/import_cours.py
(adapter l'import `from cours.models import Cours` si ton app
contenant le modèle Cours porte un autre nom).

⚠️ Lancer import_departements AVANT cette commande, sauf pour les
lignes "Préparatoire" qui n'ont volontairement aucun département
(departement = None), le préparatoire étant un niveau transversal
et non un département académique.

Usage :
    python manage.py import_cours /chemin/vers/cursus.csv
"""

import csv

from django.core.management.base import BaseCommand, CommandError

from applications.departements.models import Departement
from applications.cours.models import Cours


class Command(BaseCommand):
    help = "Importe les cours depuis un fichier CSV (departement,niveau,code,cours,credits,optionnel)."

    # Nom du département (colonne CSV) -> code du modèle Departement
    # None = pas de département (cas du Préparatoire)
    DEPARTEMENT_MAP = {
        "Communication": "COMM",
        "Psychologie": "PSY",
        "Sociologie": "SOCIO",
        "Travail Social": "TS",
        "Préparatoire": None,
    }

    # Nom du niveau (colonne CSV) -> valeur du choix CHOIX_ANNEE du modèle Cours
    NIVEAU_MAP = {
        "Préparatoire": "PREPARATOIRE",
        "Niveau I": "NIVEAU1",
        "Niveau II": "NIVEAU2",
        "Niveau III": "NIVEAU3",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path", type=str, help="Chemin vers le fichier cursus.csv"
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        try:
            fichier = open(csv_path, newline="", encoding="utf-8")
        except FileNotFoundError:
            raise CommandError(f"Fichier introuvable : {csv_path}")

        # Cache pour éviter une requête DB par ligne
        cache_departements = {}

        crees = 0
        maj = 0
        ignores = 0

        with fichier:
            lecteur = csv.DictReader(fichier)
            for num_ligne, ligne in enumerate(lecteur, start=2):
                nom_departement = (ligne.get("departement") or "").strip()
                nom_niveau = (ligne.get("niveau") or "").strip()
                code = (ligne.get("code") or "").strip()
                nom_cours = (ligne.get("cours") or "").strip()
                credits_str = (ligne.get("credits") or "").strip()
                optionnel = (ligne.get("optionnel") or "").strip().lower() == "oui"

                if not code:
                    self.stdout.write(
                        self.style.WARNING(f"Ligne {num_ligne} : code manquant, ignorée.")
                    )
                    ignores += 1
                    continue

                if nom_departement not in self.DEPARTEMENT_MAP:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ligne {num_ligne} : département inconnu « {nom_departement} », "
                            f"cours {code} ignoré."
                        )
                    )
                    ignores += 1
                    continue

                code_departement = self.DEPARTEMENT_MAP[nom_departement]
                departement = None

                if code_departement is not None:
                    if code_departement not in cache_departements:
                        try:
                            cache_departements[code_departement] = Departement.objects.get(
                                code=code_departement
                            )
                        except Departement.DoesNotExist:
                            cache_departements[code_departement] = None
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Département « {code_departement} » introuvable en base "
                                    f"(as-tu lancé import_departements ?)."
                                )
                            )
                    departement = cache_departements[code_departement]
                # Sinon (Préparatoire) : departement reste None, comme demandé.

                niveau = self.NIVEAU_MAP.get(nom_niveau)
                if niveau is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ligne {num_ligne} : niveau inconnu « {nom_niveau} », "
                            f"cours {code} ignoré."
                        )
                    )
                    ignores += 1
                    continue

                try:
                    credits = int(credits_str) if credits_str else 0
                except ValueError:
                    credits = 0

                description = "Cours optionnel." if optionnel else ""

                cours_obj, created = Cours.objects.update_or_create(
                    code=code,
                    defaults={
                        "nom": nom_cours,
                        "credits": credits,
                        "departement": departement,
                        "niveau": niveau,
                        "description": description,
                    },
                )

                if created:
                    crees += 1
                else:
                    maj += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTerminé. {crees} cours créé(s), {maj} mis à jour, {ignores} ignoré(s)."
            )
        )