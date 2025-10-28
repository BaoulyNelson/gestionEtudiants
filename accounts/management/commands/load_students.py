import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
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
                skipped_count = 0
                error_count = 0
                
                # === Tracking pour détecter les doublons dans le CSV ===
                processed_emails = set()
                processed_student_numbers = set()
                processed_phone_numbers = set()

                for row_num, row in enumerate(reader, start=2):  # start=2 car ligne 1 = header
                    email = row['email'].strip().lower()
                    student_number = row['student_number'].strip()
                    phone_number = row.get('phone_number', '').strip()
                    
                    # === VÉRIFICATION DOUBLONS EMAIL ===
                    if email in processed_emails:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : email {email} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # === VÉRIFICATION DOUBLONS STUDENT_NUMBER ===
                    if student_number in processed_student_numbers:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : student_number {student_number} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # === VÉRIFICATION DOUBLONS PHONE_NUMBER ===
                    if phone_number and phone_number in processed_phone_numbers:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : phone_number {phone_number} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # === VÉRIFICATION PHONE_NUMBER EXISTANT EN BASE ===
                    if phone_number:
                        existing_user = User.objects.filter(phone_number=phone_number).first()
                        if existing_user and existing_user.email.lower() != email:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'⊘ Ligne {row_num} ignorée : phone_number {phone_number} déjà utilisé '
                                    f'par {existing_user.get_full_name()} ({existing_user.email})'
                                )
                            )
                            skipped_count += 1
                            continue
                    
                    # === VÉRIFICATION STUDENT_NUMBER EXISTANT EN BASE ===
                    existing_student = Student.objects.filter(student_number=student_number).first()
                    if existing_student and existing_student.user.email.lower() != email:
                        self.stdout.write(
                            self.style.ERROR(
                                f'⊘ Ligne {row_num} ignorée : student_number {student_number} déjà utilisé '
                                f'par {existing_student.user.get_full_name()} ({existing_student.user.email})'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # Marquer comme traité
                    processed_emails.add(email)
                    processed_student_numbers.add(student_number)
                    if phone_number:
                        processed_phone_numbers.add(phone_number)

                    try:
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
                                'phone_number': phone_number if phone_number else '',
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
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Utilisateur créé: {user.get_full_name()} (ligne {row_num})'
                                )
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'↻ Utilisateur existant: {user.get_full_name()} (ligne {row_num})'
                                )
                            )

                        # === Profil étudiant ===
                        student, student_created = Student.objects.get_or_create(
                            user=user,
                            defaults={
                                'student_number': student_number,
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
                            updated = False
                            fields_to_update = []
                            
                            if department and student.department != department:
                                student.department = department
                                fields_to_update.append('department')
                                updated = True
                            
                            if row.get('current_year'):
                                new_year = int(row['current_year'])
                                if student.current_year != new_year:
                                    student.current_year = new_year
                                    fields_to_update.append('current_year')
                                    updated = True
                            
                            if updated:
                                try:
                                    student.save(update_fields=fields_to_update)
                                    self.stdout.write(
                                        self.style.NOTICE(
                                            f'↺ Profil mis à jour: {student.student_number} '
                                            f'({", ".join(fields_to_update)})'
                                        )
                                    )
                                except IntegrityError as e:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f'✗ Erreur mise à jour ligne {row_num}: {str(e)}'
                                        )
                                    )
                                    error_count += 1
                                    continue
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Étudiant créé: {student.student_number}'
                                )
                            )

                    except IntegrityError as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Erreur d\'intégrité ligne {row_num}: {str(e)}'
                            )
                        )
                        error_count += 1
                        continue
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Erreur inattendue ligne {row_num}: {str(e)}'
                            )
                        )
                        error_count += 1
                        continue

                # === Résumé final ===
                summary_parts = [
                    f'{created_count} nouveaux utilisateurs',
                    f'{updated_count} mis à jour'
                ]
                
                if skipped_count > 0:
                    summary_parts.append(f'{skipped_count} ignorés (doublons)')
                
                if error_count > 0:
                    summary_parts.append(f'{error_count} erreurs')
                    self.stdout.write(
                        self.style.ERROR(
                            f'\n✗ Import terminé avec {error_count} erreur(s)'
                        )
                    )
                
                if skipped_count > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n⚠️  {skipped_count} doublon(s) ignoré(s)'
                        )
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Import terminé : {", ".join(summary_parts)}.'
                    )
                )

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"✗ Fichier introuvable : {file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✗ Erreur lors de l'import : {e}"))
            raise  # Re-raise pour voir le traceback complet en développement