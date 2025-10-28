import csv
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from departments.models import Department
from accounts.models import Professor


class Command(BaseCommand):
    help = 'Charge les départements depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/departments.csv',
            help='Chemin vers le fichier CSV des départements'
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
                    code = row['code'].strip().upper()
                    name = row['name'].strip()
                    
                    # === VÉRIFICATION DOUBLONS CODE ===
                    if code in processed_codes:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : code {code} déjà traité (doublon CSV)'
                            )
                        )
                        skipped_count += 1
                        continue
                    
                    # Vérifier que les champs essentiels sont présents
                    if not code or not name:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ Ligne {row_num} ignorée : champs obligatoires manquants'
                            )
                        )
                        error_count += 1
                        continue
                    
                    # Marquer comme traité
                    processed_codes.add(code)

                    try:
                        # Récupérer le head_of_department si spécifié
                        head_of_department = None
                        head_id = row.get('head_of_department', '').strip()
                        
                        if head_id:
                            try:
                                # Chercher le professeur par ID
                                head_of_department = Professor.objects.get(id=int(head_id))
                            except (Professor.DoesNotExist, ValueError):
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'⚠️  Ligne {row_num} : Chef de département {head_id} introuvable pour {code}'
                                    )
                                )
                                # On continue quand même sans chef

                        # Création ou mise à jour du département
                        department, created = Department.objects.update_or_create(
                            code=code,
                            defaults={
                                'name': name,
                                'description': row.get('description', '').strip(),
                                'head_of_department': head_of_department,
                            }
                        )

                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Département créé: {code} - {name} (ligne {row_num})'
                                )
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'↻ Département mis à jour: {code} - {name} (ligne {row_num})'
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
                    f'{created_count} départements créés',
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
            raise