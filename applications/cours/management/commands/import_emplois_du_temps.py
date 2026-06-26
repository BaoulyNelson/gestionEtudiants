"""
Commande d'import des emplois du temps (sections de cours) depuis les
fichiers emploi_du_temps_<departement>_niveau<N>.csv (ou
emploi_du_temps_preparatoire.csv).

Format CSV attendu (en-tête obligatoire) :
    jour,heure_debut,heure_fin,code_cours,cours,prenom_prof,nom_prof,departement,niveau,session

Emplacement attendu : cours/management/commands/import_emplois_du_temps.py
(même app que import_cours.py)

⚠️ Prérequis, dans l'ordre :
    1. python manage.py import_departements
    2. python manage.py import_cours cursus.csv
    3. cette commande (les cours doivent déjà exister, on les retrouve par leur `code`)

Le département et le niveau sont déduits automatiquement du NOM DU FICHIER
(et non de la colonne "departement"/"niveau" du CSV, qui n'est que de
l'information d'affichage). Le code croise ensuite cette déduction avec le
département/niveau réel du Cours en base (importé depuis cursus.csv) : en
cas de désaccord, la ligne est rejetée plutôt qu'importée à l'aveugle.

Hypothèses prises par défaut (à ajuster si besoin) :
    - Les professeurs n'existent pas encore en base : ils sont créés à la
      volée (Utilisateur + Professeur) avec :
        * email   : prenom.nom@<--email-domaine>  (auto, dédupliqué si collision)
        * identifiant_professeur : PROF00001, PROF00002, ... (séquentiel)
        * mot de passe initial   : --mot-de-passe-defaut (identique pour tous ;
          doit_changer_mot_de_passe=True force un changement à la 1ère connexion)
        * genre   : 'M' par défaut (le modèle ne permet pas de le déduire
          du CSV de façon fiable) — à corriger manuellement si besoin
        * date_embauche : date du jour de l'import
      Un même prénom+nom (insensible à la casse) n'est créé qu'une seule
      fois ; si le compte ou le profil existe déjà, il est réutilisé.
    - numero_section (absent du CSV, mais obligatoire) est généré à partir
      du jour + heure de début, ex: "LUN0700" → stable et réexécutable
      sans créer de doublons (idempotent).
    - --annee et --semestre ne sont pas dans le CSV : ils sont passés en
      argument car ils dépendent de la période académique en cours.

Usage :
    python manage.py import_emplois_du_temps emploi_du_temps_communication_niveau1.csv --annee 2026 --semestre AUTOMNE
    python manage.py import_emplois_du_temps . --annee 2026 --semestre AUTOMNE --dry-run
    python manage.py import_emplois_du_temps . --annee 2026 --semestre AUTOMNE
        (traite tous les emploi_du_temps_*.csv du dossier courant)
"""

import csv
import datetime
import glob
import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from applications.departements.models import Departement
from applications.cours.models import Cours, SectionCours
from applications.comptes.models import Utilisateur, Professeur


class _StopDryRun(Exception):
    """Exception interne utilisée uniquement pour annuler la transaction en --dry-run."""
    pass


class Command(BaseCommand):
    help = "Importe les sections de cours (emplois du temps) depuis un ou plusieurs fichiers CSV."

    # Nom du fichier -> déduction département + niveau
    FICHIER_REGEX = re.compile(r'^emploi_du_temps_(?P<slug>[a-zA-Z-]+)(?:_niveau(?P<niveau>\d))?\.csv$')

    
    SLUG_DEPARTEMENT = {
    "psychologie":           "PSY",
    "communication-sociale": "COMM",  # ✅ mis à jour
    "sociologie":            "SOCIO",
    "travail-social":        "TS",
    "preparatoire":          None,
}

    NIVEAU_DIGIT_MAP = {"1": "NIVEAU1", "2": "NIVEAU2", "3": "NIVEAU3"}

    JOUR_ABBREV = {
        "LUNDI": "LUN", "MARDI": "MAR", "MERCREDI": "MER",
        "JEUDI": "JEU", "VENDREDI": "VEN", "SAMEDI": "SAM",
    }

    SESSION_REGEX = re.compile(r'^session(\d+)$')

    # ── Arguments ────────────────────────────────────────────────────────────

    def add_arguments(self, parser):
        parser.add_argument(
            "chemins", nargs="+",
            help="Fichier(s) CSV emploi_du_temps_*.csv, ou dossier(s) les contenant.",
        )
        parser.add_argument("--annee", type=int, required=True, help="Année académique, ex: 2026")
        parser.add_argument(
            "--semestre", required=True, choices=["AUTOMNE", "PRINTEMPS", "ETE"],
        )
        parser.add_argument(
            "--email-domaine", default="ueh.edu.ht",
            help="Domaine utilisé pour générer les emails des nouveaux professeurs.",
        )
        parser.add_argument(
            "--mot-de-passe-defaut", default="motdepasse123",
            help="Mot de passe initial des nouveaux comptes professeur.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Simule l'import (affiche le résumé) sans rien enregistrer en base.",
        )

    # ── Point d'entrée ───────────────────────────────────────────────────────

    def handle(self, *args, **options):
        fichiers = self._resoudre_fichiers(options["chemins"])
        if not fichiers:
            raise CommandError("Aucun fichier emploi_du_temps_*.csv trouvé.")

        self._cache_departements = {}
        self._cache_professeurs = {}
        self._cache_cours = {}
        self._numeros_utilises = {}
        self._profs_crees = []
        self._stats = {
            "lignes_traitees": 0,
            "sections_creees": 0,
            "sections_maj": 0,
            "ignorees_cours_introuvable": 0,
            "ignorees_incoherence": 0,
            "ignorees_format": 0,
            "erreurs_inattendues": 0,
        }

        try:
            with transaction.atomic():
                for chemin in fichiers:
                    self._traiter_fichier(chemin, options)

                self._afficher_resume(options)

                if options["dry_run"]:
                    raise _StopDryRun()
        except _StopDryRun:
            self.stdout.write(self.style.WARNING(
                "\n[DRY-RUN] Aucune donnée n'a été enregistrée en base. "
                "Relance sans --dry-run pour appliquer ces changements."
            ))

    # ── Résolution des fichiers à traiter ───────────────────────────────────

    def _resoudre_fichiers(self, chemins):
        resultats = []
        for chemin in chemins:
            if os.path.isdir(chemin):
                trouves = sorted(glob.glob(os.path.join(chemin, "emploi_du_temps_*.csv")))
                if not trouves:
                    self.stdout.write(self.style.WARNING(f"Aucun emploi_du_temps_*.csv dans « {chemin} »."))
                resultats.extend(trouves)
            elif os.path.isfile(chemin):
                resultats.append(chemin)
            else:
                raise CommandError(f"Chemin introuvable : {chemin}")
        return resultats

    # ── Déduction département/niveau depuis le nom de fichier ──────────────

    def _deduire_departement_niveau(self, nom_fichier):
        m = self.FICHIER_REGEX.match(nom_fichier)
        if not m:
            raise ValueError(
                "nom de fichier non reconnu (attendu "
                "emploi_du_temps_<departement>_niveau<1|2|3>.csv ou "
                "emploi_du_temps_preparatoire.csv)"
            )

        slug = m.group("slug").lower()
        niveau_digit = m.group("niveau")

        if slug not in self.SLUG_DEPARTEMENT:
            raise ValueError(
                f"département inconnu « {slug} » (connus : {', '.join(self.SLUG_DEPARTEMENT)})"
            )

        code_departement = self.SLUG_DEPARTEMENT[slug]

        if slug == "preparatoire":
            if niveau_digit is not None:
                raise ValueError("le préparatoire ne doit pas avoir de suffixe _niveauN")
            niveau = "PREPARATOIRE"
        else:
            if niveau_digit not in self.NIVEAU_DIGIT_MAP:
                raise ValueError("suffixe _niveau1/_niveau2/_niveau3 manquant ou invalide")
            niveau = self.NIVEAU_DIGIT_MAP[niveau_digit]

        return code_departement, niveau

    # ── Caches / lookups ─────────────────────────────────────────────────────

    def _obtenir_departement(self, code):
        if code is None:
            return None
        if code not in self._cache_departements:
            try:
                self._cache_departements[code] = Departement.objects.get(code=code)
            except Departement.DoesNotExist:
                self._cache_departements[code] = None
                self.stdout.write(self.style.WARNING(
                    f"Département « {code} » introuvable en base (as-tu lancé import_departements ?)."
                ))
        return self._cache_departements[code]

    def _obtenir_cours(self, code):
        if code not in self._cache_cours:
            try:
                self._cache_cours[code] = Cours.objects.select_related("departement").get(code=code)
            except Cours.DoesNotExist:
                self._cache_cours[code] = None
        return self._cache_cours[code]

    # ── Création / récupération des professeurs ─────────────────────────────

    def _generer_email(self, prenom, nom, domaine):
        base = f"{slugify(prenom)}.{slugify(nom)}"
        email = f"{base}@{domaine}"
        compteur = 2
        while Utilisateur.objects.filter(email=email).exists():
            email = f"{base}{compteur}@{domaine}"
            compteur += 1
        return email

    def _generer_identifiant_professeur(self):
        compteur = Professeur.objects.count() + 1
        while True:
            identifiant = f"PROF{compteur:05d}"
            if not Professeur.objects.filter(identifiant_professeur=identifiant).exists():
                return identifiant
            compteur += 1

    def _obtenir_ou_creer_professeur(self, prenom, nom, departement, options):
        cle = (prenom.strip().casefold(), nom.strip().casefold())
        if cle in self._cache_professeurs:
            return self._cache_professeurs[cle]

        prenom = prenom.strip()
        nom = nom.strip()

        # 1. On retrouve d'abord un compte utilisateur existant.
        utilisateur = Utilisateur.objects.filter(
            first_name__iexact=prenom,
            last_name__iexact=nom,
            role="PROFESSEUR",
        ).first()

        # 2. Si aucun utilisateur n'existe, on le crée.
        if utilisateur is None:
            email = self._generer_email(prenom, nom, options["email_domaine"])
            utilisateur = Utilisateur.objects.create_user(
                email=email,
                password=options["mot_de_passe_defaut"],
                first_name=prenom,
                last_name=nom,
                role="PROFESSEUR",
            )

        # 3. On récupère le profil Professeur lié à cet utilisateur,
        #    ou on le crée s'il manque.
        professeur, created = Professeur.objects.get_or_create(
            utilisateur=utilisateur,
            defaults={
                "identifiant_professeur": self._generer_identifiant_professeur(),
                "departement": departement,
                "date_embauche": datetime.date.today(),
            },
        )

        # Si le profil existait déjà, on s'assure au moins que le département
        # soit renseigné quand il était vide.
        if not created and departement is not None and professeur.departement_id is None:
            professeur.departement = departement
            professeur.save(update_fields=["departement"])

        self._cache_professeurs[cle] = professeur
        if created:
            self._profs_crees.append((professeur.identifiant_professeur, prenom, nom, utilisateur.email))
        return professeur

    # ── Génération du numero_section (absent du CSV) ────────────────────────

    def _generer_numero_section(self, code_cours, jour, heure_debut):
        base = f"{self.JOUR_ABBREV[jour]}{heure_debut.strftime('%H%M')}"
        utilises = self._numeros_utilises.setdefault(code_cours, set())
        numero = base
        suffixe = 2
        while numero in utilises:
            numero = f"{base[:7]}-{suffixe}"
            suffixe += 1
        utilises.add(numero)
        return numero

    # ── Traitement d'un fichier ──────────────────────────────────────────────

    def _traiter_fichier(self, chemin, options):
        nom_fichier = os.path.basename(chemin)
        self.stdout.write(f"\n→ {nom_fichier}")

        try:
            code_departement, niveau_attendu = self._deduire_departement_niveau(nom_fichier)
        except ValueError as exc:
            self.stdout.write(self.style.ERROR(f"  Fichier ignoré : {exc}"))
            return

        departement_attendu = self._obtenir_departement(code_departement)

        try:
            fichier = open(chemin, newline="", encoding="utf-8")
        except FileNotFoundError:
            raise CommandError(f"Fichier introuvable : {chemin}")

        with fichier:
            lecteur = csv.DictReader(fichier)
            for num_ligne, ligne in enumerate(lecteur, start=2):
                self._stats["lignes_traitees"] += 1
                self._traiter_ligne(
                    ligne, num_ligne, nom_fichier,
                    departement_attendu, niveau_attendu, options,
                )

    # ── Traitement d'une ligne ───────────────────────────────────────────────

    def _traiter_ligne(self, ligne, num_ligne, nom_fichier, departement_attendu, niveau_attendu, options):
        prefixe = f"  Ligne {num_ligne}"

        jour = (ligne.get("jour") or "").strip().upper()
        code_cours = (ligne.get("code_cours") or "").strip()
        prenom_prof = (ligne.get("prenom_prof") or "").strip()
        nom_prof = (ligne.get("nom_prof") or "").strip()
        session_brute = (ligne.get("session") or "").strip().lower()

        if jour not in self.JOUR_ABBREV:
            self.stdout.write(self.style.WARNING(f"{prefixe} : jour invalide « {jour} », ignorée."))
            self._stats["ignorees_format"] += 1
            return

        try:
            heure_debut = datetime.datetime.strptime((ligne.get("heure_debut") or "").strip(), "%H:%M").time()
            heure_fin = datetime.datetime.strptime((ligne.get("heure_fin") or "").strip(), "%H:%M").time()
        except ValueError:
            self.stdout.write(self.style.WARNING(f"{prefixe} : heure invalide, ignorée."))
            self._stats["ignorees_format"] += 1
            return

        m = self.SESSION_REGEX.match(session_brute)
        if not m:
            self.stdout.write(self.style.WARNING(f"{prefixe} : session invalide « {session_brute} », ignorée."))
            self._stats["ignorees_format"] += 1
            return
        session = f"SESSION_{m.group(1)}"
        if session not in dict(SectionCours.CHOIX_SESSION):
            self.stdout.write(self.style.WARNING(
                f"{prefixe} : session « {session} » non gérée par le modèle, ignorée."
            ))
            self._stats["ignorees_format"] += 1
            return

        cours = self._obtenir_cours(code_cours)
        if cours is None:
            self.stdout.write(self.style.WARNING(
                f"{prefixe} : cours « {code_cours} » introuvable (as-tu lancé import_cours ?), ignorée."
            ))
            self._stats["ignorees_cours_introuvable"] += 1
            return

        # Vérification de cohérence : ce que dit le nom du fichier doit
        # correspondre à ce qui est réellement enregistré pour ce cours.
        departement_cours_code = cours.departement.code if cours.departement else None
        departement_attendu_code = departement_attendu.code if departement_attendu else None
        if cours.niveau != niveau_attendu or departement_cours_code != departement_attendu_code:
            self.stdout.write(self.style.ERROR(
                f"{prefixe} : incohérence — {code_cours} est enregistré comme "
                f"{cours.get_niveau_display()} / {departement_cours_code or 'aucun département'} "
                f"(cursus.csv), mais apparaît dans « {nom_fichier} » "
                f"({niveau_attendu} / {departement_attendu_code or 'aucun département'}). Ignorée."
            ))
            self._stats["ignorees_incoherence"] += 1
            return

        if not prenom_prof or not nom_prof:
            self.stdout.write(self.style.WARNING(f"{prefixe} : professeur manquant pour {code_cours}, ignorée."))
            self._stats["ignorees_format"] += 1
            return

        try:
            professeur = self._obtenir_ou_creer_professeur(prenom_prof, nom_prof, departement_attendu, options)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f"{prefixe} : échec récupération/création professeur {prenom_prof} {nom_prof} : {exc}"
            ))
            self._stats["erreurs_inattendues"] += 1
            return

        numero_section = self._generer_numero_section(code_cours, jour, heure_debut)

        try:
            section, created = SectionCours.objects.update_or_create(
                cours=cours,
                jour_semaine=jour,
                heure_debut=heure_debut,
                semestre=options["semestre"],
                annee=options["annee"],
                defaults={
                    "numero_section": numero_section,
                    "professeur": professeur,
                    "heure_fin": heure_fin,
                    "session": session,
                },
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"{prefixe} : échec enregistrement section {code_cours} : {exc}"))
            self._stats["erreurs_inattendues"] += 1
            return

        if created:
            self._stats["sections_creees"] += 1
        else:
            self._stats["sections_maj"] += 1

    # ── Résumé final ─────────────────────────────────────────────────────────

    def _afficher_resume(self, options):
        s = self._stats
        prefixe = "[DRY-RUN] " if options["dry_run"] else ""
        self.stdout.write(self.style.SUCCESS(
            f"\n{prefixe}Terminé. {s['lignes_traitees']} ligne(s) lues — "
            f"{s['sections_creees']} section(s) créée(s), {s['sections_maj']} mise(s) à jour."
        ))

        total_ignorees = (
            s["ignorees_cours_introuvable"] + s["ignorees_incoherence"]
            + s["ignorees_format"] + s["erreurs_inattendues"]
        )
        if total_ignorees:
            self.stdout.write(self.style.WARNING(
                f"{total_ignorees} ligne(s) ignorée(s) : "
                f"{s['ignorees_cours_introuvable']} cours introuvable, "
                f"{s['ignorees_incoherence']} incohérence département/niveau, "
                f"{s['ignorees_format']} format invalide, "
                f"{s['erreurs_inattendues']} erreur inattendue."
            ))

        if self._profs_crees:
            self.stdout.write(self.style.SUCCESS(f"\n{len(self._profs_crees)} professeur(s) créé(s) :"))
            for identifiant, prenom, nom, email in self._profs_crees:
                self.stdout.write(f"  {identifiant} — {prenom} {nom} — {email}")
            self.stdout.write(self.style.WARNING(
                "Mot de passe initial identique pour tous (voir --mot-de-passe-defaut) ; "
                "doit_changer_mot_de_passe=True force un changement à la 1ère connexion."
            ))