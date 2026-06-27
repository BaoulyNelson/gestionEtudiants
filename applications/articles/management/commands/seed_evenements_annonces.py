"""
Commande de management Django : seed_evenements_annonces
Place ce fichier dans :
  applications/articles/management/commands/seed_evenements_annonces.py
(crée les dossiers management/ et commands/ avec des __init__.py vides si absents)

Usage :
  python manage.py seed_evenements_annonces
  python manage.py seed_evenements_annonces --vider   # supprime tout avant d'insérer
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from applications.articles.models import Evenement, Annonce


# ─── Données fictives ─────────────────────────────────────────────────────────

EVENEMENTS = [

    # ── À VENIR (date_debut > maintenant) ────────────────────────────────────
    {
        "titre": "Conférence internationale sur le droit haïtien",
        "description": (
            "Cette conférence réunira des juristes, magistrats et universitaires "
            "pour débattre des réformes du système judiciaire haïtien. "
            "Des intervenants de la CARICOM, de l'OEA et de l'UEH prendront la parole."
        ),
        "lieu": "Amphithéâtre principal — FASCH",
        "delta_debut":  timedelta(days=12),
        "delta_fin":    timedelta(days=13),
    },
    {
        "titre": "Journée portes ouvertes — Faculté de Droit",
        "description": (
            "Les futurs étudiants et leurs familles sont invités à découvrir les "
            "programmes, les infrastructures et les débouchés professionnels offerts "
            "par la Faculté de Droit et des Sciences Économiques d'État d'Haïti."
        ),
        "lieu": "Campus central, Port-au-Prince",
        "delta_debut":  timedelta(days=20),
        "delta_fin":    timedelta(days=20, hours=8),
    },
    {
        "titre": "Atelier de rédaction académique en créole haïtien",
        "description": (
            "Animé par le département de linguistique, cet atelier pratique vise à "
            "outiller les étudiants dans la rédaction de travaux académiques "
            "en créole haïtien selon les normes universitaires."
        ),
        "lieu": "Salle B-204 — Bâtiment des Sciences Humaines",
        "delta_debut":  timedelta(days=35),
        "delta_fin":    timedelta(days=35, hours=6),
    },
    {
        "titre": "Séminaire : Économie bleue et développement côtier en Haïti",
        "description": (
            "Ce séminaire interdisciplinaire explore les opportunités économiques "
            "liées aux ressources marines haïtiennes : pêche durable, tourisme côtier, "
            "aquaculture et gestion des aires marines protégées."
        ),
        "lieu": "Salle de conférence — Rectorat UEH",
        "delta_debut":  timedelta(days=50),
        "delta_fin":    timedelta(days=51),
    },

    # ── EN COURS (date_debut <= maintenant <= date_fin) ───────────────────────
    {
        "titre": "Exposition : Patrimoine architectural de Port-au-Prince",
        "description": (
            "Exposition photographique et documentaire retraçant l'évolution "
            "du patrimoine bâti de Port-au-Prince, des maisons gingerbread "
            "aux reconstructions post-séisme. Entrée libre pour les étudiants."
        ),
        "lieu": "Hall d'entrée — Bibliothèque centrale FASCH",
        "delta_debut":  timedelta(days=-3),
        "delta_fin":    timedelta(days=4),
    },
    {
        "titre": "Concours inter-facultés de plaidoirie",
        "description": (
            "Les équipes des facultés de droit de l'UEH s'affrontent dans "
            "des simulations de procès. Le jury est composé de magistrats "
            "et d'avocats du barreau de Port-au-Prince."
        ),
        "lieu": "Tribunal fictif — Salle A-101",
        "delta_debut":  timedelta(days=-1),
        "delta_fin":    timedelta(days=2),
    },

    # ── TERMINÉS (date_fin < maintenant) ─────────────────────────────────────
    {
        "titre": "Colloque : Genre et droit en Haïti — bilan et perspectives",
        "description": (
            "Ce colloque a réuni chercheuses, juristes et militantes pour faire "
            "le bilan des avancées législatives en matière d'égalité de genre "
            "et identifier les chantiers prioritaires pour les prochaines années."
        ),
        "lieu": "Amphithéâtre B — FASCH",
        "delta_debut":  timedelta(days=-30),
        "delta_fin":    timedelta(days=-28),
    },
    {
        "titre": "Forum étudiant : Intelligence artificielle et avenir du travail",
        "description": (
            "Un forum animé par des étudiants de sciences économiques sur l'impact "
            "de l'IA sur le marché du travail haïtien, avec des interventions "
            "d'experts du secteur privé et du secteur public."
        ),
        "lieu": "Salle polyvalente — Campus FASCH",
        "delta_debut":  timedelta(days=-60),
        "delta_fin":    timedelta(days=-59),
    },
    {
        "titre": "Cérémonie de remise des diplômes — Promotion 2023",
        "description": (
            "Remise officielle des diplômes de licence et de master aux diplômés "
            "de la promotion 2023. La cérémonie a rassemblé plus de 400 nouveaux "
            "diplômés et leurs familles en présence du Recteur de l'UEH."
        ),
        "lieu": "Grand amphithéâtre — Université d'État d'Haïti",
        "delta_debut":  timedelta(days=-90),
        "delta_fin":    timedelta(days=-89, hours=-20),
    },
]


ANNONCES = [

    # ── ACTIVES (est_active=True) ─────────────────────────────────────────────
    {
        "titre": "Inscriptions ouvertes — Semestre Automne 2025",
        "contenu": (
            "Les inscriptions pour le semestre Automne 2025 sont officiellement ouvertes "
            "du 1er au 30 juillet 2025. Les étudiants doivent se connecter au portail "
            "universitaire pour compléter leur dossier d'inscription. "
            "Les frais d'inscription doivent être réglés avant la date limite. "
            "Aucune inscription ne sera acceptée après le 30 juillet."
        ),
        "organisateur": "Bureau des Inscriptions — FASCH",
        "lieu": "Portail en ligne et Bureau des inscriptions",
        "delta_evenement": timedelta(days=15),
        "est_active": True,
    },
    {
        "titre": "Recrutement : Assistants de recherche pour le département d'économie",
        "contenu": (
            "Le département d'économie recherche quatre (4) assistants de recherche "
            "pour l'année académique 2025-2026. Profil recherché : étudiant en master "
            "ou en fin de licence, ayant de bonnes bases en statistiques et en économétrie. "
            "Dossier à déposer au secrétariat du département avant le 15 août 2025."
        ),
        "organisateur": "Département d'Économie — FASCH",
        "lieu": "Secrétariat du Département d'Économie, Bureau 112",
        "delta_evenement": timedelta(days=25),
        "est_active": True,
    },
    {
        "titre": "Rappel : Soumission des travaux de fin de semestre",
        "contenu": (
            "Tous les étudiants sont rappelés à soumettre leurs travaux de fin de semestre "
            "au plus tard le vendredi 18 juillet 2025 à 23h59 via le portail académique. "
            "Aucun délai supplémentaire ne sera accordé sauf cas de force majeure dûment "
            "documenté et approuvé par le doyen. Les soumissions hors délai recevront "
            "automatiquement une pénalité de 10 points."
        ),
        "organisateur": "Décanat — FASCH",
        "lieu": None,
        "delta_evenement": timedelta(days=8),
        "est_active": True,
    },
    {
        "titre": "Bourses d'études — Appel à candidatures 2025",
        "contenu": (
            "La Fondation UEH-Solidarité lance un appel à candidatures pour ses bourses "
            "d'études destinées aux étudiants en situation de vulnérabilité socio-économique. "
            "Chaque bourse couvre les frais de scolarité et inclut une allocation mensuelle "
            "de 5 000 HTG. Conditions : être inscrit à temps plein, avoir une moyenne ≥ 70/100, "
            "fournir un justificatif de situation économique. Date limite : 31 juillet 2025."
        ),
        "organisateur": "Fondation UEH-Solidarité",
        "lieu": "Bureau des affaires sociales — Rectorat UEH",
        "delta_evenement": timedelta(days=20),
        "est_active": True,
    },
    {
        "titre": "Maintenance du portail académique — Interruption de service",
        "contenu": (
            "Le portail académique sera inaccessible le samedi 12 juillet 2025 "
            "de 00h00 à 06h00 pour des travaux de maintenance. "
            "Nous vous prions de planifier vos soumissions en conséquence. "
            "Le service sera rétabli dès 06h00. Nous nous excusons pour la gêne occasionnée."
        ),
        "organisateur": "Direction des Systèmes d'Information — FASCH",
        "lieu": None,
        "delta_evenement": timedelta(days=2),
        "est_active": True,
    },

    # ── INACTIVES (est_active=False) ──────────────────────────────────────────
    {
        "titre": "Résultats des examens du semestre Printemps 2025",
        "contenu": (
            "Les résultats des examens du semestre Printemps 2025 ont été publiés "
            "sur le portail académique. Les étudiants peuvent consulter leurs notes "
            "en se connectant avec leurs identifiants. "
            "Les demandes de révision de copie doivent être déposées avant le 10 juin 2025. "
            "Passé ce délai, aucune contestation ne sera recevable."
        ),
        "organisateur": "Bureau des Examens — FASCH",
        "lieu": None,
        "delta_evenement": timedelta(days=-10),
        "est_active": False,
    },
    {
        "titre": "Fermeture administrative — Fête nationale du 18 mai",
        "contenu": (
            "À l'occasion de la Fête du Drapeau et de l'Université (18 mai), "
            "tous les services administratifs de la FASCH seront fermés le lundi 19 mai 2025. "
            "Les cours reprennent normalement le mardi 20 mai. "
            "Bonne fête nationale à toute la communauté universitaire !"
        ),
        "organisateur": "Administration générale — FASCH",
        "lieu": None,
        "delta_evenement": timedelta(days=-40),
        "est_active": False,
    },
    {
        "titre": "Appel à projets : Fonds d'innovation pédagogique 2024",
        "contenu": (
            "L'appel à projets pour le Fonds d'Innovation Pédagogique 2024 est désormais clôturé. "
            "Nous remercions tous les enseignants et équipes qui ont soumis un dossier. "
            "Les projets retenus seront annoncés lors de la prochaine assemblée du conseil académique. "
            "Un total de 12 projets a été reçu pour 4 financements disponibles."
        ),
        "organisateur": "Vice-Rectorat à la Pédagogie — UEH",
        "lieu": None,
        "delta_evenement": timedelta(days=-75),
        "est_active": False,
    },
]


# ─── Commande ─────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Insère des événements et annonces fictifs avec des statuts variés."

    def add_arguments(self, parser):
        parser.add_argument(
            "--vider",
            action="store_true",
            help="Supprime tous les événements et annonces existants avant d'insérer.",
        )

    def handle(self, *args, **options):
        now = timezone.now()

        if options["vider"]:
            nb_ev  = Evenement.objects.count()
            nb_an  = Annonce.objects.count()
            Evenement.objects.all().delete()
            Annonce.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  {nb_ev} événement(s) et {nb_an} annonce(s) supprimés."
            ))

        # ── Événements ────────────────────────────────────────────────────────
        self.stdout.write("\n── Création des événements ──")
        ev_crees = 0

        for data in EVENEMENTS:
            debut = now + data["delta_debut"]
            fin   = now + data["delta_fin"]

            ev, created = Evenement.objects.get_or_create(
                titre=data["titre"],
                defaults={
                    "description": data["description"],
                    "lieu":        data["lieu"],
                    "date_debut":  debut,
                    "date_fin":    fin,
                }
            )

            statut = ev.get_statut()
            if created:
                ev_crees += 1
                self.stdout.write(
                    f"  ✔  [{statut:10s}]  {ev.titre[:60]}"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ~  (existait déjà) {ev.titre[:60]}")
                )

        # ── Annonces ──────────────────────────────────────────────────────────
        self.stdout.write("\n── Création des annonces ──")
        an_crees = 0

        for data in ANNONCES:
            date_ev = now + data["delta_evenement"] if data.get("delta_evenement") else None
            est_active = data["est_active"]

            an, created = Annonce.objects.get_or_create(
                titre=data["titre"],
                defaults={
                    "contenu":       data["contenu"],
                    "organisateur":  data.get("organisateur", "FASCH"),
                    "lieu":          data.get("lieu"),
                    "date_evenement": date_ev,
                    "est_active":    est_active,
                }
            )

            label = "ACTIVE  " if est_active else "INACTIVE"
            if created:
                an_crees += 1
                self.stdout.write(f"  ✔  [{label}]  {an.titre[:60]}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ~  (existait déjà) {an.titre[:60]}")
                )

        # ── Résumé ────────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n✅  {ev_crees} événement(s) et {an_crees} annonce(s) créés avec succès.\n"
            f"    Répartition événements : 4 à venir · 2 en cours · 3 terminés\n"
            f"    Répartition annonces   : 5 actives · 3 inactives"
        ))