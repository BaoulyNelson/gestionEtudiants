from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from .models import User, Student, Professor
from departments.models import Department
from datetime import date


class UserModelTest(TestCase):
    """Tests pour le modèle User"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='motdepasse123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
    
    def test_user_creation(self):
        """Test de création d'utilisateur"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertTrue(self.user.is_student())
        self.assertFalse(self.user.is_professor())
    
    def test_user_string_representation(self):
        """Test de la représentation string"""
        expected = f"Test User (Étudiant)"
        self.assertEqual(str(self.user), expected)


class StudentModelTest(TestCase):
    """Tests pour le modèle Student"""
    
    def setUp(self):
        self.department = Department.objects.create(
            code='PSYCHO',
            name='Psychologie'
        )
        
        self.user = User.objects.create_user(
            email='student@example.com',
            password='motdepasse123',
            first_name='John',
            last_name='Doe',
            role='STUDENT'
        )
        
        self.student = Student.objects.create(
            user=self.user,
            student_number='STU001',
            department=self.department,
            current_year=1,
            enrollment_date=date.today()
        )
    
    def test_student_creation(self):
        """Test de création d'étudiant"""
        self.assertEqual(self.student.student_number, 'STU001')
        self.assertEqual(self.student.department, self.department)
        self.assertEqual(self.student.current_year, 1)
    
    def test_student_string_representation(self):
        """Test de la représentation string"""
        expected = "STU001 - John Doe"
        self.assertEqual(str(self.student), expected)


class LoginViewTest(TestCase):
    """Tests pour la vue de connexion"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='motdepasse123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
        self.user.must_change_password = False
        self.user.save()
    
    def test_login_page_status_code(self):
        """Test du code de statut de la page de connexion"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
    
    def test_login_with_valid_credentials(self):
        """Test de connexion avec des identifiants valides"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'motdepasse123'
        })
        self.assertEqual(response.status_code, 302)  # Redirection
    
    def test_login_with_invalid_credentials(self):
        """Test de connexion avec des identifiants invalides"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email ou mot de passe incorrect')


class PasswordChangeTest(TestCase):
    """Tests pour le changement de mot de passe"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='oldpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
        self.user.must_change_password = True
        self.user.save()
        self.client.login(email='test@example.com', password='oldpass123')
    
    def test_password_change_required(self):
        """Test que le changement de mot de passe est requis"""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('accounts:change_password'))
    
    def test_password_change_success(self):
        """Test du changement de mot de passe réussi"""
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'oldpass123',
            'new_password1': 'newpass123!',
            'new_password2': 'newpass123!'
        })
        
        # Recharger l'utilisateur
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)


class UserPermissionsTest(TestCase):
    """Tests pour les permissions utilisateur"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un étudiant
        self.student_user = User.objects.create_user(
            email='student@example.com',
            password='motdepasse123',
            first_name='Student',
            last_name='Test',
            role='STUDENT'
        )
        self.student_user.must_change_password = False
        self.student_user.save()
        
        # Créer un admin
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='motdepasse123',
            first_name='Admin',
            last_name='Test',
            role='ADMIN'
        )
        self.admin_user.must_change_password = False
        self.admin_user.save()
    
    def test_student_cannot_access_admin_pages(self):
        """Test qu'un étudiant ne peut pas accéder aux pages admin"""
        self.client.login(email='student@example.com', password='motdepasse123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 302)  # Redirection
    
    def test_admin_can_access_admin_pages(self):
        """Test qu'un admin peut accéder aux pages admin"""
        self.client.login(email='admin@example.com', password='motdepasse123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)