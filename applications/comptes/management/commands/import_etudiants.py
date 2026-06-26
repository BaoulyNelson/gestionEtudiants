"""
Commande d'import des étudiants depuis un fichier CSV.

Format CSV attendu (en-tête obligatoire) :
    last_name,first_name,email,password,role,genre,numero_etudiant,departement,niveau

Emplacement attendu :
    applications/comptes/management/commands/import_etudiants.py

⚠️ Prérequis, dans l'ordre :
    1. python manage.py import_departements
    2. cette commande

Le script est idempotent : un étudiant déjà importé (retrouvé par
`numero_etudiant`) est mis à jour, pas dupliqué.

Usage :
    python manage.py import_etudiants etudiants.csv
    python manage.py import_etudiants etudiants.csv --dry-run
    python manage.py import_etudiants etudiants.csv --mot-de-passe-defaut motdepasse123
"""

import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone

from applications.comptes.models import Utilisateur, Etudiant
from applications.departements.models import Departement


class _StopDryRun(Exception):
    """Exception interne : annule la transaction en mode --dry-run."""
    pass


class Command(BaseCommand):
    help = "Importe les étudiants depuis un fichier CSV."

    # Colonne CSV "departement" → code du modèle Departement
    DEPARTEMENT_MAP = {
        "Communication Sociale": "COMM",
        "Communication":         "COMM",
        "Psychologie":           "PSY",
        "Sociologie":            "SOCIO",
        "Travail Social":        "TS",
        "Travail social":        "TS",
    }

    # Colonne CSV "niveau" → valeur CHOIX_ANNEE du modèle Etudiant
    NIVEAU_MAP = {
        "PREPARATOIRE": "PREPARATOIRE",
        "NIVEAU1":      "NIVEAU1",
        "NIVEAU2":      "NIVEAU2",
        "NIVEAU3":      "NIVEAU3",
        # Formes alternatives acceptées
        "Préparatoire": "PREPARATOIRE",
        "Niveau I":     "NIVEAU1",
        "Niveau II":    "NIVEAU2",
        "Niveau III":   "NIVEAU3",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Chemin vers le fichier CSV (ex: etudiants.csv)",
        )
        parser.add_argument(
            "--mot-de-passe-defaut",
            default="motdepasse123",
            help="Mot de passe utilisé si la colonne 'password' est vide.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule l'import sans rien enregistrer en base.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        dry_run  = options["dry_run"]

        try:
            open(csv_path, newline="", encoding="utf-8").close()
        except FileNotFoundError:
            raise CommandError(f"Fichier introuvable : {csv_path}")

        self._cache_departements = {}
        self._stats = {
            "crees":      0,
            "mis_a_jour": 0,
            "ignores":    0,
        }

        try:
            with transaction.atomic():
                # ── Désactivation du signal post_save pendant l'import ──────
                # Le signal creer_ou_mettre_a_jour_profil tente un get_or_create
                # sur Etudiant à chaque save() de l'Utilisateur, ce qui entre en
                # conflit avec notre gestion manuelle du profil et déclenche une
                # ValidationError (date_inscription null, utilisateur déjà lié).
                # On gère le profil Etudiant nous-mêmes : le signal est inutile ici.
                from applications.comptes.signals import creer_ou_mettre_a_jour_profil
                post_save.disconnect(creer_ou_mettre_a_jour_profil, sender=get_user_model())

                try:
                    self._importer(csv_path, options)
                finally:
                    # Reconnexion du signal dans tous les cas (succès ou exception)
                    post_save.connect(creer_ou_mettre_a_jour_profil, sender=get_user_model())

                self._afficher_resume(dry_run)

                if dry_run:
                    raise _StopDryRun()

        except _StopDryRun:
            self.stdout.write(self.style.WARNING(
                "\n[DRY-RUN] Aucune donnée enregistrée. "
                "Relancez sans --dry-run pour appliquer."
            ))

    # ── Import principal ─────────────────────────────────────────────────────

    def _importer(self, csv_path, options):
        mdp_defaut = options["mot_de_passe_defaut"]

        with open(csv_path, newline="", encoding="utf-8") as fichier:
            lecteur = csv.DictReader(fichier)

            for num_ligne, ligne in enumerate(lecteur, start=2):

                # ── Lecture des colonnes ──────────────────────────────────
                last_name       = (ligne.get("last_name")       or "").strip()
                first_name      = (ligne.get("first_name")      or "").strip()
                email           = (ligne.get("email")           or "").strip()
                password        = (ligne.get("password")        or mdp_defaut).strip() or mdp_defaut
                genre           = (ligne.get("genre")           or "M").strip().upper()
                numero_etudiant = (ligne.get("numero_etudiant") or "").strip()
                nom_departement = (ligne.get("departement")     or "").strip()
                nom_niveau      = (ligne.get("niveau")          or "").strip()

                # ── Validations minimales ─────────────────────────────────
                if not numero_etudiant:
                    self.stdout.write(self.style.WARNING(
                        f"Ligne {num_ligne} : numero_etudiant manquant, ignorée."
                    ))
                    self._stats["ignores"] += 1
                    continue

                if not email:
                    self.stdout.write(self.style.WARNING(
                        f"Ligne {num_ligne} : email manquant pour {last_name} {first_name}, ignorée."
                    ))
                    self._stats["ignores"] += 1
                    continue

                # ── Département ───────────────────────────────────────────
                code_dep = self.DEPARTEMENT_MAP.get(nom_departement)
                if code_dep is None:
                    self.stdout.write(self.style.WARNING(
                        f"Ligne {num_ligne} : département inconnu "
                        f"« {nom_departement} » — {numero_etudiant} ignoré."
                    ))
                    self._stats["ignores"] += 1
                    continue

                departement = self._obtenir_departement(code_dep, num_ligne)
                if departement is None:
                    self._stats["ignores"] += 1
                    continue

                # ── Niveau ────────────────────────────────────────────────
                niveau = self.NIVEAU_MAP.get(nom_niveau)
                if niveau is None:
                    self.stdout.write(self.style.WARNING(
                        f"Ligne {num_ligne} : niveau inconnu « {nom_niveau} » "
                        f"— {numero_etudiant} ignoré."
                    ))
                    self._stats["ignores"] += 1
                    continue

                # ── Genre ─────────────────────────────────────────────────
                if genre not in ("M", "F"):
                    genre = "M"  # valeur par défaut silencieuse

                # ── Création / mise à jour ────────────────────────────────
                try:
                    self._creer_ou_mettre_a_jour(
                        num_ligne=num_ligne,
                        last_name=last_name,
                        first_name=first_name,
                        email=email,
                        password=password,
                        genre=genre,
                        numero_etudiant=numero_etudiant,
                        departement=departement,
                        niveau=niveau,
                    )
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(
                        f"Ligne {num_ligne} : erreur inattendue pour "
                        f"{numero_etudiant} — {exc}"
                    ))
                    self._stats["ignores"] += 1

    # ── Création / mise à jour d'un étudiant ─────────────────────────────────

    def _creer_ou_mettre_a_jour(self, num_ligne, last_name, first_name, email,
                                  password, genre, numero_etudiant,
                                  departement, niveau):
        """
        Crée ou met à jour le couple Utilisateur + Etudiant.
        Recherche par `numero_etudiant` (idempotent).

        Le signal post_save est déconnecté avant l'appel à cette méthode :
        on gère le profil Etudiant manuellement via update_fields ciblés,
        ce qui évite toute ValidationError liée à date_inscription.
        """
        # ── Vérification de l'email (unicité) ────────────────────────────
        email_final = email
        if (Utilisateur.objects.filter(email=email_final)
                               .exclude(profil_etudiant__numero_etudiant=numero_etudiant)
                               .exists()):
            base, domaine = email.rsplit("@", 1)
            suffixe = 2
            while Utilisateur.objects.filter(email=email_final).exists():
                email_final = f"{base}{suffixe}@{domaine}"
                suffixe += 1
            self.stdout.write(self.style.WARNING(
                f"  Email « {email} » déjà utilisé — remplacé par « {email_final} »."
            ))

        # ── Étudiant déjà présent ? ───────────────────────────────────────
        try:
            etudiant = Etudiant.objects.select_related("utilisateur").get(
                numero_etudiant=numero_etudiant
            )
            utilisateur = etudiant.utilisateur

            # Mise à jour des champs Utilisateur
            # (le signal est déconnecté : pas de déclenchement de get_or_create)
            utilisateur.last_name  = last_name
            utilisateur.first_name = first_name
            utilisateur.genre      = genre
            utilisateur.save(update_fields=["last_name", "first_name", "genre"])

            # Mise à jour des champs Etudiant — on bypasse full_clean() via
            # QuerySet.update() pour éviter la revalidation de date_inscription
            # (déjà correctement définie en base lors de la création initiale).
            Etudiant.objects.filter(pk=etudiant.pk).update(
                departement=departement,
                niveau=niveau,
            )

            self._stats["mis_a_jour"] += 1

        except Etudiant.DoesNotExist:
            # ── Création de l'Utilisateur ─────────────────────────────────
            utilisateur = Utilisateur.objects.create_user(
                email=email_final,
                password=password,
                first_name=first_name,
                last_name=last_name,
                genre=genre,
                role="ETUDIANT",
                doit_changer_mot_de_passe=True,
            )

            # ── Création du profil Etudiant ───────────────────────────────
            # On contourne Etudiant.save() → full_clean() en utilisant
            # directement le manager pour éviter toute contrainte de validation
            # non pertinente à l'import (le signal est déjà déconnecté).
            Etudiant.objects.create(
                utilisateur=utilisateur,
                numero_etudiant=numero_etudiant,
                departement=departement,
                niveau=niveau,
                date_inscription=timezone.now().date(),
            )

            self._stats["crees"] += 1

    # ── Cache département ─────────────────────────────────────────────────────

    def _obtenir_departement(self, code, num_ligne):
        if code not in self._cache_departements:
            try:
                self._cache_departements[code] = Departement.objects.get(code=code)
            except Departement.DoesNotExist:
                self._cache_departements[code] = None
                self.stdout.write(self.style.WARNING(
                    f"Ligne {num_ligne} : département « {code} » introuvable "
                    f"(as-tu lancé import_departements ?)."
                ))
        return self._cache_departements[code]

    # ── Résumé final ──────────────────────────────────────────────────────────

    def _afficher_resume(self, dry_run):
        s      = self._stats
        prefixe = "[DRY-RUN] " if dry_run else ""
        total  = s["crees"] + s["mis_a_jour"] + s["ignores"]

        self.stdout.write(self.style.SUCCESS(
            f"\n{prefixe}Terminé. {total} ligne(s) lues — "
            f"{s['crees']} étudiant(s) créé(s), "
            f"{s['mis_a_jour']} mis à jour, "
            f"{s['ignores']} ignoré(s)."
        ))