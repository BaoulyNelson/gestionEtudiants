import csv
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from courses.models import Course, CourseSection
from accounts.models import Professor


class Command(BaseCommand):
    help = "Importe les sections de cours à partir d’un fichier CSV (cours, professeur, horaire, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Chemin vers le fichier CSV à importer'
        )

    def safe_get(self, row, key, default=''):
        """Retourne proprement la valeur d’un champ CSV"""
        return row.get(key, '').strip() or default

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file']
        created, updated, errors = 0, 0, 0

        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        course_code = self.safe_get(row, 'course_code')
                        section_number = self.safe_get(row, 'section_number')
                        professor_code = self.safe_get(row, 'professor_id')

                        # --- Récupération du cours ---
                        try:
                            course = Course.objects.get(code=course_code)
                        except Course.DoesNotExist:
                            self.stderr.write(f"⚠️  Cours introuvable : {course_code}")
                            errors += 1
                            continue

                        # --- Récupération du professeur ---
                        professor = None
                        if professor_code:
                            try:
                                professor = Professor.objects.get(professor_id=professor_code)
                            except Professor.DoesNotExist:
                                self.stderr.write(f"⚠️  Professeur introuvable : {professor_code}")

                        # --- Conversion des champs temporels ---
                        start_time = datetime.datetime.strptime(self.safe_get(row, 'start_time', '00:00'), '%H:%M').time()
                        end_time = datetime.datetime.strptime(self.safe_get(row, 'end_time', '00:00'), '%H:%M').time()

                        if start_time >= end_time:
                            self.stderr.write(f"⚠️  Horaire invalide : {course_code} {section_number} ({start_time} >= {end_time})")
                            errors += 1
                            continue

                        # --- Lecture autres champs ---
                        is_open = self.safe_get(row, 'is_open', 'true').lower() == 'true'
                        max_students = int(self.safe_get(row, 'max_students', '30'))
                        year = int(self.safe_get(row, 'year', '2025'))

                        session = self.safe_get(row, 'session', 'SESSION_1')
                        semester = self.safe_get(row, 'semester', 'FALL')
                        day_of_week = self.safe_get(row, 'day_of_week', 'LUNDI')
                        room = self.safe_get(row, 'room', '')

                        # --- Création ou mise à jour ---
                        section, created_flag = CourseSection.objects.update_or_create(
                            course=course,
                            section_number=section_number,
                            professor=professor,
                            session=session,
                            semester=semester,
                            year=year,
                            defaults={
                                'day_of_week': day_of_week,
                                'start_time': start_time,
                                'end_time': end_time,
                                'room': room,
                                'max_students': max_students,
                                'is_open': is_open,
                            }
                        )

                        if created_flag:
                            created += 1
                            self.stdout.write(f"✅ Section créée : {section}")
                        else:
                            updated += 1
                            self.stdout.write(f"↻ Section mise à jour : {section}")

                    except Exception as e:
                        self.stderr.write(f"❌ Erreur à la ligne : {row} → {e}")
                        errors += 1

        except FileNotFoundError:
            raise CommandError(f"Fichier non trouvé : {file_path}")

        # --- Résumé final ---
        self.stdout.write(self.style.SUCCESS(
            f"\n--- Import terminé ---\n"
            f"✅ {created} créées\n"
            f"↻ {updated} mises à jour\n"
            f"⚠️ {errors} erreurs\n"
        ))
