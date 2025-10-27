
# ========== grades/management/commands/load_grades.py ==========
import csv
from django.core.management.base import BaseCommand
from grades.models import Grade
from enrollments.models import Enrollment
from accounts.models import Student, Professor
from courses.models import Course, CourseSection
from departments.models import Department
from datetime import datetime
from django.conf import settings
from accounts.models import User


class Command(BaseCommand):
    help = 'Charge les notes depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/grades.csv',
            help='Chemin vers le fichier CSV des notes'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                created_count = 0
                updated_count = 0
                
                for row in reader:
                    try:
                        student = Student.objects.get(student_number=row['student_number'])
                        course = Course.objects.get(code=row['course_code'])
                        
                        section = CourseSection.objects.get(
                            course=course,
                            section_number=row['section_number']
                        )
                        
                        enrollment = Enrollment.objects.get(
                            student=student,
                            course_section=section
                        )
                        
                        grade, created = Grade.objects.update_or_create(
                            enrollment=enrollment,
                            defaults={
                                'midterm_exam': float(row['midterm_exam']) if row.get('midterm_exam') else None,
                                'final_exam': float(row['final_exam']) if row.get('final_exam') else None,
                                'assignments': float(row['assignments']) if row.get('assignments') else None,
                                'participation': float(row['participation']) if row.get('participation') else None,
                                'project': float(row['project']) if row.get('project') else None,
                                'comments': row.get('comments', ''),
                                'graded_by': section.professor,
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Note créée: {student.student_number} - '
                                    f'{course.code} = {grade.final_grade}'
                                )
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'↻ Note mise à jour: {student.student_number} - '
                                    f'{course.code} = {grade.final_grade}'
                                )
                            )
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Erreur ligne: {row} - {str(e)}')
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