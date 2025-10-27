# ========== enrollments/management/commands/load_enrollments.py ==========
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from enrollments.models import Enrollment
from accounts.models import Student
from courses.models import Course, CourseSection


class Command(BaseCommand):
    help = 'Charge les inscriptions depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/enrollments.csv',
            help='Chemin vers le fichier CSV des inscriptions'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                created_count = 0
                skipped_count = 0
                
                for row in reader:
                    try:
                        student = Student.objects.get(student_number=row['student_number'])
                        course = Course.objects.get(code=row['course_code'])
                        
                        section = CourseSection.objects.get(
                            course=course,
                            section_number=row['section_number'],
                            session=row['session'],
                            semester=row['semester'],
                            year=int(row['year'])
                        )
                        
                        enrollment, created = Enrollment.objects.get_or_create(
                            student=student,
                            course_section=section,
                            defaults={
                                'status': row['status'],
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Inscription créée: {student.student_number} -> '
                                    f'{section.course.code}-{section.section_number}'
                                )
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⊘ Inscription existante: {student.student_number} -> '
                                    f'{section.course.code}-{section.section_number}'
                                )
                            )
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Erreur ligne: {row} - {str(e)}')
                        )
                        skipped_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Import terminé: {created_count} créés, {skipped_count} ignorés'
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




