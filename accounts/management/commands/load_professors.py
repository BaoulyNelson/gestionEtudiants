import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
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
                skipped_count = 0
                error_count = 0
                
                # === Tracking pour détecter les doublons dans le CSV ===
                processed_emails = set()
                processed_professor_ids = set()

                for row_num, row in enumerate(reader, start=2):  # start=2 car ligne 1 = header
                    email = row['email'].strip().lower()
                    prof_id = row.get('professor_id', '').strip()
                    
                    # === VÉRIFICATION DOUBLONS EMAIL ===
                    if email in processed_emails:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : email {email} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # === VÉRIFICATION DOUBLONS PROFESSOR_ID ===
                    if prof_id and prof_id in processed_professor_ids:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : professor_id {prof_id} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # === VÉRIFICATION PROFESSOR_ID EXISTANT EN BASE ===
                    if prof_id:
                        existing_prof = Professor.objects.filter(professor_id=prof_id).first()
                        if existing_prof and existing_prof.user.email.lower() != email:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'⊘ Ligne {row_num} ignorée : professor_id {prof_id} déjà utilisé '
                                    f'par {existing_prof.user.get_full_name()} ({existing_prof.user.email})'
                                )
                            )
                            skipped_count += 1
                            continue
                    
                    # Marquer comme traité
                    processed_emails.add(email)
                    if prof_id:
                        processed_professor_ids.add(prof_id)

                    try:
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
                            self.stdout.write(self.style.SUCCESS(f'✓ Utilisateur créé: {user.get_full_name()} (ligne {row_num})'))
                        else:
                            updated_count += 1
                            self.stdout.write(self.style.WARNING(f'↻ Utilisateur existant: {user.get_full_name()} (ligne {row_num})'))

                        # === Profil professeur ===
                        professor, prof_created = Professor.objects.get_or_create(
                            user=user,
                            defaults={
                                'professor_id': prof_id if prof_id else None,
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
                            fields_to_update = []
                            
                            if department and professor.department != department:
                                professor.department = department
                                fields_to_update.append('department')
                                updated = True
                            
                            if row.get('specialization') and professor.specialization != row['specialization']:
                                professor.specialization = row['specialization']
                                fields_to_update.append('specialization')
                                updated = True
                            
                            # Mise à jour du professor_id seulement si vide ou différent
                            if prof_id and (not professor.professor_id or professor.professor_id != prof_id):
                                professor.professor_id = prof_id
                                fields_to_update.append('professor_id')
                                updated = True
                            
                            if updated:
                                try:
                                    professor.save(update_fields=fields_to_update)
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'→ Professeur mis à jour: {professor.user.get_full_name()} '
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

                        # === Résumé par ligne ===
                        if prof_created:
                            self.stdout.write(self.style.SUCCESS(f'✓ Professeur créé: {professor.user.get_full_name()}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'↻ Professeur existant: {professor.user.get_full_name()}'))

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
                    f'{created_count} utilisateurs créés',
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
            self.stdout.write(self.style.ERROR(f'✗ Fichier non trouvé: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {str(e)}'))
            raise  # Re-raise pour voir le traceback complet en développement