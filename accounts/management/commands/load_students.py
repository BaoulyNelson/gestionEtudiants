import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from accounts.models import User, Student
from departments.models import Department


class Command(BaseCommand):
    help = 'Charge les étudiants depuis un fichier CSV (création/mise à jour)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/students.csv',
            help='Chemin vers le fichier CSV des étudiants'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                created_count = 0
                updated_count = 0

                for row in reader:
                    # === Département ===
                    department = None
                    if row.get('department_code'):
                        code = row['department_code'].strip().upper()
                        name = dict(Department.DEPARTMENT_CHOICES).get(code, code)
                        department, _ = Department.objects.get_or_create(
                            code=code,
                            defaults={
                                'name': name,
                                'description': f"Département de {name.lower()}."
                            }
                        )

                    # === Utilisateur étudiant ===
                    user, user_created = User.objects.get_or_create(
                        email=row['email'].strip(),
                        defaults={
                            'first_name': row['first_name'].strip(),
                            'last_name': row['last_name'].strip(),
                            'role': 'STUDENT',
                            'phone_number': row.get('phone_number', '').strip(),
                            'date_of_birth': (
                                datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date()
                                if row.get('date_of_birth') else None
                            ),
                            'is_active': True,
                            'must_change_password': True,
                        }
                    )

                    if user_created:
                        temp_password = getattr(settings, "DEFAULT_TEMP_PASSWORD", "Temp1234!")
                        user.set_password(temp_password)
                        user.save()
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Utilisateur créé: {user.get_full_name()}'))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(f'↻ Utilisateur existant: {user.get_full_name()}'))

                    # === Profil étudiant ===
                    student, student_created = Student.objects.get_or_create(
                        user=user,
                        defaults={
                            'student_number': row['student_number'].strip(),
                            'department': department,
                            'current_year': int(row['current_year']) if row.get('current_year') else 1,
                            'enrollment_date': (
                                datetime.strptime(row['enrollment_date'], '%Y-%m-%d').date()
                                if row.get('enrollment_date') else timezone.now().date()
                            ),
                        }
                    )

                    if not student_created:
                        # Mise à jour des champs si nécessaires
                        student.department = department
                        student.current_year = int(row['current_year']) if row.get('current_year') else student.current_year
                        student.save(update_fields=['department', 'current_year'])
                        self.stdout.write(self.style.NOTICE(f'↺ Profil mis à jour: {student.student_number}'))

                self.stdout.write(self.style.SUCCESS(
                    f"\nImport terminé : {created_count} nouveaux utilisateurs, {updated_count} mis à jour."
                ))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erreur lors de l'import : {e}"))
