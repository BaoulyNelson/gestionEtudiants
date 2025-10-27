# ========== courses/management/commands/load_courses.py ==========
import csv
from django.core.management.base import BaseCommand
from courses.models import Course
from departments.models import Department


class Command(BaseCommand):
    help = 'Charge les cours depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/courses.csv',
            help='Chemin vers le fichier CSV des cours'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    # Vérifie que les champs essentiels sont là
                    if not row.get('code') or not row.get('name'):
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Ligne ignorée (incomplète) : {row}"
                        ))
                        error_count += 1
                        continue

                    # Tente de récupérer le département
                    department = None
                    dept_code = row.get('department_code')
                    if dept_code:
                        try:
                            department = Department.objects.get(code=dept_code)
                        except Department.DoesNotExist:
                            self.stdout.write(self.style.ERROR(
                                f"✗ Département introuvable ({dept_code}) pour le cours {row['code']}"
                            ))
                            error_count += 1
                            continue

                    # Convertir les champs numériques en toute sécurité
                    try:
                        credits = int(row.get('credits', 0))
                    except ValueError:
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Crédit invalide pour {row['code']} : {row['credits']}"
                        ))
                        credits = 0

                    try:
                        year_level = int(row.get('year_level', 1))
                    except ValueError:
                        year_level = 1

                    # Création ou mise à jour du cours
                    course, created = Course.objects.update_or_create(
                        code=row['code'],
                        defaults={
                            'name': row['name'],
                            'description': row.get('description', ''),
                            'credits': credits,
                            'department': department,
                            'year_level': year_level,
                            'is_active': True,
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"✓ Cours créé : {course.code} - {course.name}"
                        ))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(
                            f"↻ Cours mis à jour : {course.code} - {course.name}"
                        ))

            # Résumé
            self.stdout.write(self.style.SUCCESS(
                f"\nImport terminé : {created_count} créés, {updated_count} mis à jour, {error_count} erreurs."
            ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"✗ Fichier non trouvé : {file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erreur inattendue : {str(e)}"))
