import csv
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from courses.models import Course, CourseSection
from accounts.models import Professor


class Command(BaseCommand):
    help = "Importe les sections de cours à partir d’un fichier CSV"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Chemin vers le fichier CSV')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file']
        created, updated, errors = 0, 0, 0

        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        course_code = row['course_code'].strip()
                        section_number = row['section_number'].strip()
                        professor_code = row['professor_id'].strip()
                        
                        # Récupérer le cours
                        try:
                            course = Course.objects.get(code=course_code)
                        except Course.DoesNotExist:
                            self.stderr.write(f"⚠️  Cours introuvable: {course_code}")
                            errors += 1
                            continue
                        
                        # Récupérer le professeur
                        try:
                            professor = Professor.objects.get(professor_id=professor_code)
                        except Professor.DoesNotExist:
                            self.stderr.write(f"⚠️  Professeur introuvable: {professor_code}")
                            professor = None  # On laisse NULL si non trouvé

                        # Conversion des champs
                        start_time = datetime.datetime.strptime(row['start_time'], '%H:%M').time()
                        end_time = datetime.datetime.strptime(row['end_time'], '%H:%M').time()
                        is_open = row['is_open'].strip().lower() == 'true'
                        max_students = int(row['max_students'])
                        year = int(row['year'])

                        section, created_flag = CourseSection.objects.update_or_create(
                            course=course,
                            section_number=section_number,
                            session=row['session'].strip(),
                            semester=row['semester'].strip(),
                            year=year,
                            defaults={
                                'professor': professor,
                                'day_of_week': row['day_of_week'].strip(),
                                'start_time': start_time,
                                'end_time': end_time,
                                'room': row['room'].strip(),
                                'max_students': max_students,
                                'is_open': is_open,
                            }
                        )

                        if created_flag:
                            created += 1
                            self.stdout.write(f"✓ Section créée : {section}")
                        else:
                            updated += 1
                            self.stdout.write(f"↻ Section mise à jour : {section}")

                    except Exception as e:
                        self.stderr.write(f"❌ Erreur ligne: {row} → {e}")
                        errors += 1

        except FileNotFoundError:
            raise CommandError(f"Fichier non trouvé : {file_path}")

        self.stdout.write(self.style.SUCCESS(
            f"\nImport terminé : {created} créées, {updated} mises à jour, {errors} erreurs."
        ))
