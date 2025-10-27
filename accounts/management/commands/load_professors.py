import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from accounts.models import User, Professor
from departments.models import Department


class Command(BaseCommand):
    help = 'Charge les professeurs depuis un fichier CSV (création/mise à jour)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/professors.csv',
            help='Chemin vers le fichier CSV des professeurs'
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
                        # Nom complet à partir des choix du modèle
                        name = dict(Department.DEPARTMENT_CHOICES).get(code, code)
                        department, _ = Department.objects.get_or_create(
                            code=code,
                            defaults={
                                'name': name,
                                'description': f"Département de {name.lower()}."
                            }
                        )

                    # === Utilisateur (professeur) ===
                    user, user_created = User.objects.get_or_create(
                        email=row['email'].strip(),
                        defaults={
                            'first_name': row['first_name'].strip(),
                            'last_name': row['last_name'].strip(),
                            'role': 'PROFESSOR',
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

                    # === Profil professeur ===
                    professor, prof_created = Professor.objects.get_or_create(
                        user=user,
                        defaults={
                            'professor_id': row.get('professor_id'),
                            'department': department,
                            'specialization': row.get('specialization', '').strip(),
                            'hire_date': (
                                datetime.strptime(row['hire_date'], '%Y-%m-%d').date()
                                if row.get('hire_date') else timezone.now().date()
                            ),
                        }
                    )

                    # === Mise à jour des données existantes ===
                    if not prof_created:
                        updated = False
                        if department and professor.department != department:
                            professor.department = department
                            updated = True
                        if row.get('specialization') and professor.specialization != row['specialization']:
                            professor.specialization = row['specialization']
                            updated = True
                        if row.get('professor_id') and professor.professor_id != row['professor_id']:
                            professor.professor_id = row['professor_id']
                            updated = True
                        if updated:
                            professor.save()
                            self.stdout.write(self.style.SUCCESS(f'→ Professeur mis à jour: {professor.user.get_full_name()}'))

                    # === Résumé ===
                    if prof_created:
                        self.stdout.write(self.style.SUCCESS(f'✓ Professeur créé: {professor.user.get_full_name()}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'↻ Professeur existant: {professor.user.get_full_name()}'))

                # === Résumé final ===
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nImport terminé : {created_count} utilisateurs créés, {updated_count} mis à jour.'
                    )
                )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ Fichier non trouvé: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {str(e)}'))
