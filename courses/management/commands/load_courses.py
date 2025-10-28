import csv
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
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
                processed_codes = set()

                for row_num, row in enumerate(reader, start=2):  # start=2 car ligne 1 = header
                    # Vérifie que les champs essentiels sont là
                    if not row.get('code') or not row.get('name'):
                        self.stdout.write(
                            self.style.WARNING(
                                f"⊘ Ligne {row_num} ignorée : champs obligatoires manquants"
                            )
                        )
                        error_count += 1
                        continue

                    code = row['code'].strip().upper()
                    
                    # === VÉRIFICATION DOUBLONS CODE ===
                    if code in processed_codes:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : code {code} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # Marquer comme traité
                    processed_codes.add(code)

                    try:
                        # Tente de récupérer le département
                        department = None
                        dept_code = row.get('department_code', '').strip().upper()
                        
                        if dept_code:
                            try:
                                department = Department.objects.get(code=dept_code)
                            except Department.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"✗ Ligne {row_num} ignorée : Département {dept_code} introuvable pour {code}"
                                    )
                                )
                                error_count += 1
                                continue

                        # Convertir les champs numériques en toute sécurité
                        try:
                            credits = int(row.get('credits', 0))
                        except ValueError:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠️  Ligne {row_num} : Crédit invalide pour {code}, utilisation de 0"
                                )
                            )
                            credits = 0

                        try:
                            year_level = int(row.get('year_level', 1))
                        except ValueError:
                            year_level = 1

                        # Création ou mise à jour du cours
                        course, created = Course.objects.update_or_create(
                            code=code,
                            defaults={
                                'name': row['name'].strip(),
                                'description': row.get('description', '').strip(),
                                'credits': credits,
                                'department': department,
                                'year_level': year_level,
                                'is_active': True,
                            }
                        )

                        if created:
                            created_count += 1
                            dept_info = f" ({department.code})" if department else " (sans département)"
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Cours créé : {course.code} - {course.name}{dept_info} (ligne {row_num})"
                                )
                            )
                        else:
                            updated_count += 1
                            dept_info = f" ({department.code})" if department else " (sans département)"
                            self.stdout.write(
                                self.style.WARNING(
                                    f"↻ Cours mis à jour : {course.code} - {course.name}{dept_info} (ligne {row_num})"
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
                    f'{created_count} cours créés',
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
            self.stdout.write(self.style.ERROR(f"✗ Fichier non trouvé : {file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erreur inattendue : {str(e)}"))
            raise