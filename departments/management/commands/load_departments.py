import csv
from django.core.management.base import BaseCommand
from departments.models import Department


class Command(BaseCommand):
    help = 'Charge les départements depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/departments.csv',
            help='Chemin vers le fichier CSV des départements'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                created_count = 0
                updated_count = 0
                
                for row in reader:
                    department, created = Department.objects.update_or_create(
                        code=row['code'],
                        defaults={
                            'name': row['name'],
                            'description': row.get('description', ''),
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Département créé: {department.name}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'↻ Département mis à jour: {department.name}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Import terminé: {created_count} créés, {updated_count} mis à jour'
                    )
                )
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'✗ Fichier non trouvé: {file_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Erreur: {str(e)}')
            )


