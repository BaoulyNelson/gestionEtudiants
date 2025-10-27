from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import date, time
from accounts.models import User, Student, Professor
from departments.models import Department
from courses.models import Course, CourseSection
from enrollments.models import Enrollment


class EnrollmentModelTest(TestCase):
    """Tests pour le modèle Enrollment"""
    
    def setUp(self):
        # Créer un département
        self.department = Department.objects.create(
            code='PSYCHO',
            name='Psychologie'
        )
        
        # Créer un étudiant
        self.student_user = User.objects.create_user(
            email='student@example.com',
            password='testpass123',
            first_name='Student',
            last_name='Test',
            role='STUDENT'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_number='STU001',
            department=self.department,
            current_year=1,
            enrollment_date=date.today()
        )
        
        # Créer un professeur
        self.professor_user = User.objects.create_user(
            email='prof@example.com',
            password='testpass123',
            first_name='Prof',
            last_name='Test',
            role='PROFESSOR'
        )
        self.professor = Professor.objects.create(
            user=self.professor_user,
            professor_id='PROF001',
            department=self.department,
            hire_date=date.today()
        )
        
        # Créer un cours
        self.course = Course.objects.create(
            code='PSY101',
            name='Introduction à la Psychologie',
            credits=3,
            department=self.department,
            year_level=1
        )
        
        # Créer une section
        self.section = CourseSection.objects.create(
            course=self.course,
            section_number='01',
            professor=self.professor,
            day_of_week='LUNDI',
            start_time=time(9, 0),
            end_time=time(11, 0),
            session='SESSION_1',
            semester='FALL',
            year=2024,
            max_students=30
        )
    
    def test_enrollment_creation(self):
        """Test de création d'inscription"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course_section=self.section
        )
        self.assertEqual(enrollment.status, 'ENROLLED')
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.course_section, self.section)
    
    def test_max_courses_per_session(self):
        """Test de la limite de cours par session"""
        # Créer 7 sections différentes
        for i in range(7):
            course = Course.objects.create(
                code=f'PSY10{i+2}',
                name=f'Course {i+2}',
                credits=3,
                department=self.department,
                year_level=1
            )
            section = CourseSection.objects.create(
                course=course,
                section_number='01',
                professor=self.professor,
                day_of_week='LUNDI',
                start_time=time(9 + i, 0),
                end_time=time(10 + i, 0),
                session='SESSION_1',
                semester='FALL',
                year=2024,
                max_students=30
            )
            Enrollment.objects.create(
                student=self.student,
                course_section=section
            )
        
        # Essayer de créer une 8ème inscription
        course8 = Course.objects.create(
            code='PSY109',
            name='Course 8',
            credits=3,
            department=self.department,
            year_level=1
        )
        section8 = CourseSection.objects.create(
            course=course8,
            section_number='01',
            professor=self.professor,
            day_of_week='MARDI',
            start_time=time(9, 0),
            end_time=time(10, 0),
            session='SESSION_1',
            semester='FALL',
            year=2024,
            max_students=30
        )
        
        enrollment = Enrollment(
            student=self.student,
            course_section=section8
        )
        
        with self.assertRaises(ValidationError):
            enrollment.save()
    
    def test_schedule_conflict_detection(self):
        """Test de détection des conflits d'horaire"""
        # Créer une première inscription
        Enrollment.objects.create(
            student=self.student,
            course_section=self.section
        )
        
        # Créer une section qui chevauche
        course2 = Course.objects.create(
            code='PSY102',
            name='Psychology 2',
            credits=3,
            department=self.department,
            year_level=1
        )
        section2 = CourseSection.objects.create(
            course=course2,
            section_number='01',
            professor=self.professor,
            day_of_week='LUNDI',
            start_time=time(10, 0),  # Chevauche avec 9h-11h
            end_time=time(12, 0),
            session='SESSION_1',
            semester='FALL',
            year=2024,
            max_students=30
        )
        
        enrollment2 = Enrollment(
            student=self.student,
            course_section=section2
        )
        
        with self.assertRaises(ValidationError):
            enrollment2.save()
    
    def test_section_full(self):
        """Test qu'on ne peut pas s'inscrire à une section pleine"""
        # Limiter à 2 étudiants
        self.section.max_students = 2
        self.section.save()
        
        # Créer 2 autres étudiants et les inscrire
        for i in range(2):
            user = User.objects.create_user(
                email=f'student{i}@example.com',
                password='testpass123',
                first_name=f'Student{i}',
                last_name='Test',
                role='STUDENT'
            )
            student = Student.objects.create(
                user=user,
                student_number=f'STU00{i+2}',
                department=self.department,
                current_year=1,
                enrollment_date=date.today()
            )
            Enrollment.objects.create(
                student=student,
                course_section=self.section
            )
        
        # Essayer d'inscrire un 3ème étudiant
        enrollment = Enrollment(
            student=self.student,
            course_section=self.section
        )
        
        with self.assertRaises(ValidationError):
            enrollment.save()
    
    def test_duplicate_enrollment(self):
        """Test qu'on ne peut pas s'inscrire deux fois au même cours"""
        Enrollment.objects.create(
            student=self.student,
            course_section=self.section
        )
        
        # Essayer de créer une deuxième inscription
        with self.assertRaises(Exception):  # Violation de contrainte unique
            Enrollment.objects.create(
                student=self.student,
                course_section=self.section
            )


class EnrollmentViewTest(TestCase):
    """Tests pour les vues d'inscription"""
    
    def setUp(self):
        # Configuration similaire à EnrollmentModelTest
        self.department = Department.objects.create(
            code='PSYCHO',
            name='Psychologie'
        )
        
        self.student_user = User.objects.create_user(
            email='student@example.com',
            password='testpass123',
            first_name='Student',
            last_name='Test',
            role='STUDENT'
        )
        self.student_user.must_change_password = False
        self.student_user.save()
        
        self.student = Student.objects.create(
            user=self.student_user,
            student_number='STU001',
            department=self.department,
            current_year=1,
            enrollment_date=date.today()
        )
        
        professor_user = User.objects.create_user(
            email='prof@example.com',
            password='testpass123',
            first_name='Prof',
            last_name='Test',
            role='PROFESSOR'
        )
        professor = Professor.objects.create(
            user=professor_user,
            professor_id='PROF001',
            department=self.department,
            hire_date=date.today()
        )
        
        course = Course.objects.create(
            code='PSY101',
            name='Introduction à la Psychologie',
            credits=3,
            department=self.department,
            year_level=1
        )
        
        self.section = CourseSection.objects.create(
            course=course,
            section_number='01',
            professor=professor,
            day_of_week='LUNDI',
            start_time=time(9, 0),
            end_time=time(11, 0),
            session='SESSION_1',
            semester='FALL',
            year=2024,
            max_students=30
        )
        
        self.client.login(email='student@example.com', password='testpass123')
    
    def test_available_sections_view(self):
        """Test de la vue des sections disponibles"""
        from django.urls import reverse
        response = self.client.get(reverse('enrollments:available_sections'))
        self.assertEqual(response.status_code, 200)
    
    def test_enroll_to_section(self):
        """Test d'inscription à une section"""
        from django.urls import reverse
        response = self.client.get(
            reverse('enrollments:enroll', kwargs={'section_id': self.section.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirection
        
        # Vérifier que l'inscription a été créée
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                course_section=self.section
            ).exists()
        )