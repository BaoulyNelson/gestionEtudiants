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
├── venv/
├── fasch_config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/
├── courses/
├── enrollments/
├── grades/
├── departments/
├── templates/
│   ├── base.html
│   ├── home.html
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── media/
├── data/
│   └── (fichiers CSV)
├── manage.py
├── .env
└── requirements.txt
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
python manage.py load_departments
python manage.py load_courses
python manage.py load_students
```

## Notes importantes

- Toujours activer l'environnement virtuel avant de travailler
- Ne jamais commiter le fichier .env
- Sauvegarder régulièrement la base de données
- Les mots de passe temporaires par défaut: "TempPass2024!"


accounts/management/commands/
├── load_professors.py
└── load_students.py

courses/management/commands/
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
