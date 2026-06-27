"""
Script de données de démonstration — FASCH SGU
===============================================
Place ce fichier dans le dossier racine du projet (à côté de manage.py)
puis lance :  python demo_data.py

Il crée :
  - Catégories et tags pour les articles
  - 10 articles avec statuts variés
"""

import os
import sys
import django
from pathlib import Path

# ── ROOT DU PROJET (important) ─────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# ── SETTINGS DJANGO ────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuration.settings")

django.setup()

# ── Imports après setup ───────────────────────────────────────────────────────
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from applications.articles.models import Article, Categorie, Tag

User = get_user_model()

# ══════════════════════════════════════════════════════════════════════════════
# Utilitaires
# ══════════════════════════════════════════════════════════════════════════════

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"


def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def info(msg):
    print(f"  {CYAN}→{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}!{RESET} {msg}")


def title(msg):
    print(f"\n{BOLD}{CYAN}{'━'*55}{RESET}\n{BOLD}  {msg}{RESET}\n{'━'*55}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. RÉCUPÉRATION DU SUPERUTILISATEUR EXISTANT
# ══════════════════════════════════════════════════════════════════════════════
title("1. Récupération du superutilisateur")

admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    print(f"  {RED}✗{RESET} Aucun superutilisateur trouvé.")
    print(f"  {YELLOW}!{RESET} Crée-en un avec : python manage.py createsuperuser")
    sys.exit(1)

ok(f"Superutilisateur trouvé : {admin_user.get_full_name()} ({admin_user.email})")

# Récupère un auteur quelconque pour varier (professeur ou admin)
auteur_secondaire = (
    User.objects.filter(role__in=["PROFESSEUR", "ADMIN"])
    .exclude(pk=admin_user.pk)
    .first()
    or admin_user
)


# ══════════════════════════════════════════════════════════════════════════════
# 2. CATÉGORIES
# ══════════════════════════════════════════════════════════════════════════════
title("2. Création des catégories")

CATEGORIES = [
    ("Actualités FASCH", "#dc2626", "Nouvelles et événements de la faculté", 1),
    ("Vie académique", "#2196F3", "Cours, examens, résultats et calendrier", 2),
    ("Recherche", "#4CAF50", "Publications et travaux de recherche", 3),
    ("Culture", "#FF9800", "Arts, littérature et patrimoine haïtien", 4),
    ("International", "#9C27B0", "Relations et partenariats internationaux", 5),
    ("Technologie", "#00BCD4", "Numérique, innovation et sciences sociales", 6),
]

cats = {}
for nom, couleur, desc, ordre in CATEGORIES:
    cat, created = Categorie.objects.get_or_create(
        slug=slugify(nom),
        defaults={"nom": nom, "couleur": couleur, "description": desc, "ordre": ordre},
    )
    cats[nom] = cat
    ok(f"{nom:22s} {'créée' if created else 'existante'}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. TAGS
# ══════════════════════════════════════════════════════════════════════════════
title("3. Création des tags")

TAG_NAMES = [
    "fasch",
    "ueh",
    "haïti",
    "sciences-humaines",
    "éducation",
    "recherche",
    "étudiants",
    "professeurs",
    "communication",
    "sociologie",
    "journalisme",
    "développement",
]
tags = {}
for name in TAG_NAMES:
    tag, _ = Tag.objects.get_or_create(slug=slugify(name), defaults={"nom": name})
    tags[name] = tag
ok(f"{len(tags)} tags créés / vérifiés")


# ══════════════════════════════════════════════════════════════════════════════
# 4. ARTICLES
# ══════════════════════════════════════════════════════════════════════════════
title("4. Création des articles")

now = timezone.now()

ARTICLES = [
    (
        "La FASCH lance son nouveau système de gestion universitaire",
        "Actualités FASCH",
        admin_user,
        "publie",
        True,
        True,
        0,
        ["fasch", "ueh", "éducation"],
        """<p>La Faculté des Sciences Humaines franchit un cap décisif dans sa modernisation avec le lancement officiel de son système de gestion universitaire en ligne. Ce portail permettra aux étudiants de gérer leurs inscriptions, consulter leurs notes et télécharger leurs relevés directement depuis leur espace personnel.</p>
<h2>Une transformation numérique attendue</h2>
<p>Après plusieurs mois de développement, la plateforme est désormais accessible à l'ensemble des étudiants inscrits. Elle intègre une gestion complète des cours, des sections et des évaluations.</p>
<blockquote>« Ce système représente un investissement majeur dans l'avenir numérique de notre faculté. »</blockquote>
<p>Les professeurs disposent également d'un espace dédié pour saisir les notes et communiquer avec leurs étudiants.</p>""",
    ),
    (
        "Résultats du concours d'entrée : 450 nouveaux étudiants admis",
        "Vie académique",
        auteur_secondaire,
        "publie",
        True,
        False,
        1,
        ["fasch", "étudiants", "éducation"],
        """<p>La FASCH annonce les résultats du concours d'entrée pour l'année académique en cours. Au total, 450 candidats ont été admis dans les différents départements de la faculté, sur plus de 2 000 candidatures reçues.</p>
<h2>Répartition par département</h2>
<p>Le département de <strong>Communication Graphique</strong> accueille 120 nouveaux étudiants, suivi du département de <strong>Journalisme</strong> avec 95 admis. La Sociologie et les Sciences de l'Éducation complètent le tableau avec respectivement 135 et 100 nouveaux inscrits.</p>
<p>Les admis sont invités à procéder à leur inscription définitive avant la date limite fixée au 30 du mois courant.</p>""",
    ),
    (
        "Colloque international sur les sciences sociales en Haïti",
        "Recherche",
        admin_user,
        "publie",
        True,
        False,
        3,
        ["fasch", "recherche", "haïti", "international"],
        """<p>La FASCH accueille les 15 et 16 du mois prochain un colloque international réunissant des chercheurs de 12 pays autour du thème : <em>« Sciences sociales et reconstruction en contexte post-crise »</em>.</p>
<h2>Un programme riche</h2>
<p>Plus de 40 communications scientifiques seront présentées lors de cet événement qui vise à renforcer les liens entre la recherche haïtienne et la communauté scientifique internationale.</p>
<p>Des ateliers thématiques sur la méthodologie de recherche en milieu fragile seront également organisés à l'intention des étudiants de master et de doctorat.</p>""",
    ),
    (
        "Le département de Journalisme remporte le Prix Haïti Presse 2026",
        "Actualités FASCH",
        auteur_secondaire,
        "publie",
        False,
        False,
        5,
        ["fasch", "journalisme", "haïti"],
        """<p>Les étudiants du département de Journalisme de la FASCH ont décroché le prestigieux Prix Haïti Presse 2026 dans la catégorie « Reportage d'investigation ». Ce prix récompense un travail collectif sur les conditions de vie dans les quartiers défavorisés de Port-au-Prince.</p>
<p>Cette distinction confirme la qualité de la formation dispensée au sein du département et la rigueur professionnelle inculquée aux étudiants dès leur première année.</p>""",
    ),
    (
        "Partenariat avec l'Université de Montréal : 20 bourses disponibles",
        "International",
        admin_user,
        "publie",
        False,
        False,
        7,
        ["fasch", "international", "étudiants", "développement"],
        """<p>La FASCH et l'Université de Montréal ont officialisé un accord de partenariat académique ouvrant la voie à des échanges étudiants et professoraux. Dans ce cadre, 20 bourses de mobilité sont offertes aux étudiants de master pour un séjour d'études de 6 mois à Montréal.</p>
<p>Les candidatures sont ouvertes jusqu'à la fin du mois. Les étudiants intéressés doivent soumettre un dossier complet comprenant leur relevé de notes, une lettre de motivation et deux lettres de recommandation.</p>""",
    ),
    (
        "Inauguration de la nouvelle bibliothèque numérique",
        "Actualités FASCH",
        auteur_secondaire,
        "publie",
        False,
        False,
        10,
        ["fasch", "éducation", "technologie"],
        """<p>La FASCH a inauguré sa bibliothèque numérique donnant accès à plus de 50 000 ouvrages et revues scientifiques en ligne. Cette ressource est accessible 24h/24 à tous les étudiants et professeurs munis de leur identifiant universitaire.</p>
<p>Le catalogue comprend notamment des bases de données spécialisées en sciences humaines et sociales, des thèses et mémoires haïtiens, ainsi qu'une collection d'archives historiques numérisées.</p>""",
    ),
    (
        "Calendrier des examens de fin de semestre — Session 2026",
        "Vie académique",
        admin_user,
        "publie",
        False,
        False,
        2,
        ["fasch", "étudiants", "éducation"],
        """<p>La direction des études publie le calendrier officiel des examens de fin de semestre pour la session 2026. Les épreuves se dérouleront du 15 au 30 du mois prochain selon le planning détaillé disponible sur le portail étudiant.</p>
<p>Les étudiants sont priés de vérifier leurs convocations et de signaler toute anomalie au secrétariat académique avant le début des examens. Aucune réclamation ne sera acceptée pendant la période d'évaluation.</p>""",
    ),
    (
        "La sociologie haïtienne face aux défis du XXIe siècle",
        "Recherche",
        auteur_secondaire,
        "publie",
        False,
        False,
        14,
        ["recherche", "sociologie", "haïti", "sciences-humaines"],
        """<p>Une nouvelle publication collective des professeurs du département de Sociologie explore les transformations profondes de la société haïtienne à l'ère de la mondialisation. Cet ouvrage de 320 pages est disponible au secrétariat de la faculté et en version numérique sur la bibliothèque en ligne.</p>
<p>Les auteurs analysent notamment les mutations familiales, les nouvelles formes de mobilisation citoyenne et l'impact des migrations sur l'identité culturelle haïtienne.</p>""",
    ),
    (
        "Rapport annuel 2025 — Bilan et perspectives",
        "Actualités FASCH",
        admin_user,
        "en_revision",
        False,
        False,
        0,
        ["fasch", "ueh"],
        "<p>Le rapport annuel 2025 est en cours de finalisation. Il sera publié prochainement après validation par le conseil de faculté.</p>",
    ),
    (
        "Nouveau programme de master en Communication Digitale",
        "Vie académique",
        auteur_secondaire,
        "brouillon",
        False,
        False,
        0,
        ["fasch", "communication", "technologie"],
        "<p>La FASCH prépare l'ouverture d'un nouveau master professionnel en Communication Digitale pour la rentrée 2027. Les détails du programme seront communiqués prochainement.</p>",
    ),
]

import random

count = 0
for (
    titre,
    cat_nom,
    auteur_obj,
    statut,
    une,
    breaking,
    jours,
    tag_list,
    contenu,
) in ARTICLES:
    slug = slugify(titre)
    if Article.objects.filter(slug=slug).exists():
        warn(f"Existe déjà : {titre[:55]}")
        continue
    pub_date = now - timezone.timedelta(days=jours) if statut == "publie" else None
    art = Article.objects.create(
        titre=titre,
        slug=slug,
        contenu=contenu,
        auteur=auteur_obj,
        categorie=cats.get(cat_nom),
        statut=statut,  # ← statut (pas status)
        est_a_la_une=une,
        est_breaking=breaking,
        publie_le=pub_date,
        nombre_vues=random.randint(50, 4500) if statut == "publie" else 0,
    )
    for t in tag_list:
        if t in tags:
            art.tags.add(tags[t])
    count += 1
    badge = ""
    if une:
        badge += " ⭐une"
    if breaking:
        badge += " 🔴breaking"
    ok(f"[{statut:10s}] {titre[:52]}{badge}")

info(f"{count} articles créés")


# ══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ══════════════════════════════════════════════════════════════════════════════
title("Résumé de la démonstration")

pub = Article.objects.filter(statut="publie").count()
brou = Article.objects.filter(statut="brouillon").count()
rev = Article.objects.filter(statut="en_revision").count()

print(f"""
  {BOLD}Contenu créé{RESET}
    ├── Catégories  : {Categorie.objects.count()}
    ├── Tags        : {Tag.objects.count()}
    └── Articles    : {Article.objects.count()} total  ({pub} publiés · {brou} brouillons · {rev} en révision)

  {BOLD}URLs à tester{RESET}
    ├── http://127.0.0.1:8000/
    ├── http://127.0.0.1:8000/articles/actualites/
    └── http://127.0.0.1:8000/admin/

{GREEN}{BOLD}  Données de démonstration chargées avec succès !{RESET}
""")
