# FASCH University — Plateforme de Gestion Universitaire

Application web développée avec **Django 4.2** pour la gestion complète d'un établissement universitaire : étudiants, professeurs, cours, notes, devoirs, inscriptions et plus encore.

---

## Fonctionnalités principales

- **Gestion des comptes** : authentification par email, rôles multiples (étudiant, professeur, administrateur, super-utilisateur), changement de mot de passe obligatoire à la première connexion, génération de badges
- **Cours & emplois du temps** : création de cours, sections, import d'emplois du temps via commandes de gestion
- **Inscriptions** : inscription aux sections disponibles, historique, validation administrative
- **Notes** : saisie individuelle ou groupée, relevés de notes, palmarès, GPA, statistiques, déclaration et validation de notes
- **Devoirs** : création par les professeurs, remise par les étudiants, correction et notation
- **Examens** : gestion des examens par département
- **Départements** : organisation par département, affectation des cours et enseignants
- **Articles & blog** : système éditorial avec rôles (lecteur, auteur, éditeur), commentaires
- **Notifications** : alertes sur les notes et événements
- **Portail** : tableau de bord personnalisé selon le rôle, annuaire étudiants/professeurs, recherche globale, livres, newsletter
- **Contact** : formulaire de contact intégré
- **Export PDF** : relevés de notes, palmarès et GPA exportables en PDF (WeasyPrint, xhtml2pdf)

---

## Stack technique

| Composant | Technologie |
|---|---|
| Framework | Django 4.2 |
| Base de données | MySQL (mysqlclient) |
| Authentification | Django Auth + django-allauth |
| Formulaires | django-crispy-forms + Bootstrap 5 |
| Éditeur riche | django-ckeditor |
| Génération PDF | WeasyPrint, xhtml2pdf, ReportLab |
| Paiements | django-paypal, Stripe, Moncashify |
| Tâches asynchrones | Celery + Kombu |
| API REST | Django REST Framework + drf-spectacular |
| Fichiers statiques | Whitenoise |

---

## Structure du projet

```
fasch_university/
├── applications/
│   ├── articles/         # Blog et système éditorial
│   ├── comments/         # Commentaires
│   ├── comptes/          # Authentification, profils, badges
│   ├── contact/          # Formulaire de contact
│   ├── cours/            # Cours, sections, emplois du temps
│   ├── departements/     # Départements
│   ├── devoirs/          # Devoirs et remises
│   ├── inscriptions/     # Inscriptions aux cours
│   ├── notes/            # Notes, relevés, palmarès
│   ├── notifications/    # Système de notifications
│   └── portail/          # Tableaux de bord, examens, livres
├── configuration/
│   ├── settings.py
│   └── urls.py
├── templates/            # Templates HTML par module
├── utilitaires/
│   └── roles.py          # Helpers de vérification des rôles
├── manage.py
├── requirements.txt
└── .env
```

---

## Rôles utilisateurs

| Rôle | Description |
|---|---|
| `SUPERUTILISATEUR` | Accès total à l'administration Django |
| `ADMIN` | Gestion de l'établissement (inscriptions, notes, paramètres) |
| `PROFESSEUR` | Saisie des notes, gestion des cours et devoirs |
| `ETUDIANT` | Consultation des notes, inscriptions, remise de devoirs |

Les professeurs disposent également d'un rôle éditorial (`LECTEUR`, `AUTEUR`, `EDITEUR`) pour le module articles.

---

## Installation

### Prérequis

- Python 3.10+
- MySQL 8+
- pip

### Mise en place

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd fasch_university

# 2. Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs
```

### Configuration `.env`

```env
SECRET_KEY='votre-clé-secrète'
DEBUG=True
DB_NAME=fasch_university_db
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Base de données

```bash
# Créer la base de données MySQL
mysql -u root -p -e "CREATE DATABASE fasch_university_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Appliquer les migrations
python manage.py migrate

# Créer un super-utilisateur
python manage.py createsuperuser
```

### Lancer le serveur de développement

```bash
python manage.py runserver
```

L'application est accessible sur [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Commandes de gestion

Des commandes personnalisées permettent l'import de données initiales :

```bash
# Importer des étudiants depuis un fichier
python manage.py import_etudiants

# Importer des cours
python manage.py import_cours

# Importer les emplois du temps
python manage.py import_emplois_du_temps

# Importer les emplois du temps communs
python manage.py import_emplois_du_temps_commun
```

---

## URLs principales

| Chemin | Module |
|---|---|
| `/` | Accueil du portail |
| `/tableau-de-bord/` | Tableau de bord (selon le rôle) |
| `/comptes/` | Authentification et profils |
| `/cours/` | Cours et sections |
| `/inscriptions/` | Inscriptions |
| `/notes/` | Notes et relevés |
| `/devoirs/` | Devoirs |
| `/departements/` | Départements |
| `/articles/` | Blog |
| `/portail/` | Portail administrateur |
| `/notifications/` | Notifications |
| `/contact/` | Contact |
| `/commentaires/` | Commentaires |
| `/admin/` | Administration Django |

---

## Contribution

1. Créer une branche : `git checkout -b feature/ma-fonctionnalite`
2. Committer les changements : `git commit -m "feat: description"`
3. Pousser la branche : `git push origin feature/ma-fonctionnalite`
4. Ouvrir une Pull Request

---

## Licence

Projet à usage interne — FASCH (Faculté des Sciences Humaines). Tous droits réservés.
