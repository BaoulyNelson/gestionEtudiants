# Guide d'installation - Système de gestion FASCH

## Prérequis

- Python 3.10+
- XAMPP (MySQL)
- Git

## Installation

### 1. Créer le projet Django

```bash
# Créer le dossier du projet
mkdir fasch_university
cd fasch_university

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Installer Django et dépendances
pip install django==4.2
pip install mysqlclient
pip install python-decouple
pip install pillow
```

### 2. Créer le projet Django

```bash
django-admin startproject fasch_config .
```

### 3. Créer les applications

```bash
python manage.py startapp accounts
python manage.py startapp courses
python manage.py startapp enrollments
python manage.py startapp grades
python manage.py startapp departments
```

### 4. Configuration de la base de données

1. Démarrer XAMPP et activer MySQL
2. Créer la base de données via phpMyAdmin:
   - Nom: `fasch_university_db`
   - Encodage: `utf8mb4_unicode_ci`

### 5. Créer le fichier .env

À la racine du projet, créer un fichier `.env`:

```env
SECRET_KEY=votre-cle-secrete-django-ici
DEBUG=True
DB_NAME=fasch_university_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 6. Créer le fichier .gitignore

```
venv/
*.pyc
__pycache__/
db.sqlite3
.env
media/
staticfiles/
*.log
```

### 7. Structure des dossiers

```
fasch_university/
├── comptes/
│   └── management/
│       └── commands/
├── departements/
│   └── management/
│       └── commands/
│           └── charger_departements.py
├── cours/
├── inscriptions/
├── notes/
├── templates/
│   ├── comptes/
│   │   ├── connexion.html
│   │   ├── changer_mot_de_passe.html
│   │   ├── profil.html
│   │   ├── liste_utilisateurs.html
│   │   ├── creer_utilisateur.html
│   │   └── modifier_utilisateur.html
│   ├── cours/
│   │   ├── liste_cours.html
│   │   ├── detail_cours.html
│   │   ├── formulaire_cours.html
│   │   ├── liste_sections.html
│   │   ├── detail_section.html
│   │   ├── formulaire_section.html
│   │   └── mes_cours.html
│   ├── inscriptions/
│   │   ├── mes_inscriptions.html
│   │   ├── sections_disponibles.html
│   │   ├── liste_inscriptions.html
│   │   └── historique_inscriptions.html
│   ├── notes/
│   │   ├── mes_notes.html
│   │   ├── saisie_notes.html
│   │   ├── liste_notes.html
│   │   ├── detail_note.html
│   │   ├── sections_professeur.html
│   │   ├── releve_notes.html
│   │   └── statistiques_cours.html
│   ├── base.html
│   ├── accueil.html
│   ├── tableau_bord_etudiant.html
│   ├── tableau_bord_professeur.html
│   └── tableau_bord_administrateur.html
├── static/
├── media/
├── donnees/
│   └── departements.csv
└── configuration_fasch/
    ├── settings.py
    ├── urls.py
    └── views.py
```

### 8. Appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 9. Créer le superuser

```bash
python manage.py createsuperuser
```

### 10. Collecter les fichiers statiques

```bash
python manage.py collectstatic
```

### 11. Lancer le serveur

```bash
python manage.py runserver
```

Accéder à: http://127.0.0.1:8000

## Fichier requirements.txt

```
Django==4.2
mysqlclient
python-decouple
Pillow
```

## Commandes personnalisées

```bash
# Charger les données depuis CSV
python manage.py import_emplois_du_temps . --annee 2026 --semestre AUTOMNE --dry-run
```

## Notes importantes

- Toujours activer l'environnement virtuel avant de travailler
- Ne jamais commiter le fichier .env
- Sauvegarder régulièrement la base de données
- Les mots de passe temporaires par défaut: "TempPass2024!"


accounts/management/commands/
├── load_professors.py
└── load_students.py

cours/management/commands/
├── load_courses.py
└── load_sections.py

departments/management/commands/
└── load_departments.py

enrollments/management/commands/
└── load_enrollments.py

grades/management/commands/
└── load_grades.py


python manage.py load_departments --file data/departments.csv
python manage.py load_courses --file data/courses.csv
python manage.py load_sections --file data/sections.csv
python manage.py load_professors --file data/professors.csv
python manage.py load_students --file data/students.csv
python manage.py load_enrollments --file data/enrollments.csv
python manage.py load_grades --file data/grades.csv
