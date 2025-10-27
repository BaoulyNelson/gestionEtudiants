from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from .models import User
from .forms import (
    LoginForm, ChangePasswordForm, UserCreationForm,
    StudentCreationForm, ProfessorCreationForm, AdminCreationForm,
    UserUpdateForm, StudentUpdateForm, ProfessorUpdateForm
)
from departments.models import Department
from django.db.models import Count
from enrollments.models import Enrollment
# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from accounts.models import User, Student, Professor
from courses.models import Course, CourseSection  # à adapter selon ton app
from grades.models import Grade  # à adapter selon ton app
from utils.roles import is_admin


def home_view(request):
    """Page d'accueil"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')



@login_required
def dashboard(request):
    """Tableau de bord personnalisé selon le rôle"""
    user = request.user
    context = {'user': user}
    
    if user.is_student():
        # Dashboard étudiant
        student = user.student_profile
        
        # Inscriptions actives
        active_enrollments = student.enrollments.filter(
            status='ENROLLED'
        ).select_related('course_section__course', 'course_section__professor__user')[:5]
        
        # Statistiques
        total_courses = student.enrollments.filter(status='ENROLLED').count()
        completed_courses = student.enrollments.filter(status='COMPLETED').count()
        
        # Calculer GPA
        grades = Grade.objects.filter(
            enrollment__student=student,
            enrollment__status='COMPLETED',
            final_grade__isnull=False
        )
        
        total_points = 0
        total_credits = 0
        for grade in grades:
            credits = grade.enrollment.course_section.course.credits
            grade_value = float(grade.final_grade)
            
            if grade_value >= 90:
                points = 4.0
            elif grade_value >= 80:
                points = 3.0
            elif grade_value >= 70:
                points = 2.0
            elif grade_value >= 60:
                points = 1.0
            else:
                points = 0.0
            
            total_points += points * credits
            total_credits += credits
        
        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
        
        context.update({
            'active_enrollments': active_enrollments,
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'gpa': gpa,
            'is_student': True,
        })
        
        # Utiliser votre template personnalisé
        return render(request, 'dashboards/student_dashboard.html', context)
    
    elif user.is_professor():
        # Dashboard professeur
        professor = user.professor_profile
        
        # Sections enseignées
        sections = professor.course_sections.select_related('course').annotate(
            enrolled_count=Count('enrollments', filter=Q(enrollments__status='ENROLLED'))
        )[:5]
        
        # Statistiques
        total_sections = professor.course_sections.count()
        total_students = Enrollment.objects.filter(
            course_section__professor=professor,
            status='ENROLLED'
        ).count()
        
        context.update({
            'sections': sections,
            'total_sections': total_sections,
            'total_students': total_students,
            'is_professor': True,
        })
        
        # Utiliser votre template personnalisé
        return render(request, 'dashboards/professor_dashboard.html', context)
    
    elif user.is_admin_user():
        # Dashboard administrateur
        
        # Statistiques générales
        total_students = Student.objects.filter(user__is_active=True).count()
        total_professors = Professor.objects.filter(user__is_active=True).count()
        total_courses = Course.objects.filter(is_active=True).count()
        total_enrollments = Enrollment.objects.filter(status='ENROLLED').count()
        
        # Départements
        departments = Department.objects.annotate(
            student_count=Count('students', filter=Q(students__user__is_active=True)),
            professor_count=Count('professors', filter=Q(professors__user__is_active=True))
        )
        
        # Inscriptions récentes
        recent_enrollments = Enrollment.objects.select_related(
            'student__user',
            'course_section__course'
        ).order_by('-enrollment_date')[:10]
        
        context.update({
            'total_students': total_students,
            'total_professors': total_professors,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'departments': departments,
            'recent_enrollments': recent_enrollments,
            'is_admin': True,
        })
        
        # Utiliser votre template personnalisé
        return render(request, 'dashboards/admin_dashboard.html', context)
    
    # Dashboard par défaut
    return render(request, 'dashboards/default_dashboard.html', context)







def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Bienvenue, {user.get_full_name()}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Ce compte est inactif.')
            else:
                messages.error(request, 'Identifiants incorrects.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})





def logout_view(request):
    """Vue de déconnexion avec confirmation"""
    if request.method == "POST":
        logout(request)
        messages.info(request, 'Vous avez été déconnecté avec succès.')
        return redirect('home')
    return render(request, "accounts/logout_confirm.html")



@login_required
def change_password_view(request):
    """Vue pour changer le mot de passe"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été modifié avec succès.')
            return redirect('home')
    else:
        form = ChangePasswordForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    context = {'user': request.user}
    
    if request.user.is_student():
        context['student'] = request.user.student_profile
    elif request.user.is_professor():
        context['professor'] = request.user.professor_profile
    
    return render(request, 'accounts/profile.html', context)





@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    """Liste des utilisateurs (admin uniquement)"""
    users = User.objects.all().order_by('-created_at')

    # Récupération des paramètres GET
    role = request.GET.get('role', '').strip()
    search = request.GET.get('search', '').strip()

    # Filtrage par rôle
    if role:
        users = users.filter(role=role)

    # Filtrage par recherche (nom complet inclus)
    if search:
        search_parts = search.split()
        users = users.filter(
            Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(first_name__icontains=search.split(" ")[0])
        )
        # Si l’utilisateur tape "Manon François", on gère les deux morceaux :
        if len(search_parts) == 2:
            users = users.filter(
                Q(first_name__icontains=search_parts[0], last_name__icontains=search_parts[1])
                | Q(first_name__icontains=search_parts[1], last_name__icontains=search_parts[0])
            )

    # Pagination
    paginator = Paginator(users, getattr(settings, "PAGINATION_PER_PAGE", 10))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'role_choices': User.ROLE_CHOICES,
        'current_role': role,
        'search': search,  # pour que le champ se remplisse dans le template
    }

    return render(request, 'accounts/user_list.html', context)


@login_required
@user_passes_test(is_admin)
def user_create_view(request):
    """Création d'un nouvel utilisateur (Student, Professor, Admin)"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST, request.FILES)
        role = request.POST.get('role')

        if form.is_valid():
            # Création de l'utilisateur
            user = form.save(commit=False)
            user.role = role  # ✅ Assigne le rôle sélectionné
            temp_password = getattr(settings, "DEFAULT_TEMP_PASSWORD", "motdepasse123")
            user.set_password(temp_password)
            user.must_change_password = True
            user.save()  # 🔥 Le signal crée automatiquement le profil lié

            # Message de succès avec mot de passe temporaire
            messages.success(
                request,
                f"Utilisateur {user.get_full_name()} créé avec succès. "
                f"Mot de passe temporaire : {temp_password}"
            )
            return redirect('accounts:user_list')

        else:
            messages.error(
                request,
                "Le formulaire contient des erreurs. Veuillez vérifier les champs."
            )

    else:
        form = UserCreationForm()

    context = {
        'form': form,
        'roles': ['STUDENT', 'PROFESSOR', 'ADMIN'],  # Pour rendre le choix du rôle dans le template
    }
    return render(request, 'accounts/user_create.html', context)



@login_required
@user_passes_test(is_admin)
def user_update_view(request, user_id):
    """Modification d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            form.save()
            
            # Mettre à jour le profil selon le rôle
            if user.is_student():
                student_form = StudentUpdateForm(
                    request.POST, 
                    instance=user.student_profile
                )
                if student_form.is_valid():
                    student_form.save()
            
            elif user.is_professor():
                professor_form = ProfessorUpdateForm(
                    request.POST, 
                    instance=user.professor_profile
                )
                if professor_form.is_valid():
                    professor_form.save()
            
            messages.success(request, 'Utilisateur modifié avec succès.')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user)
        
        # Charger le bon formulaire de profil
        profile_form = None
        if user.is_student():
            profile_form = StudentUpdateForm(instance=user.student_profile)
        elif user.is_professor():
            profile_form = ProfessorUpdateForm(instance=user.professor_profile)
    
    context = {
        'form': form,
        'profile_form': profile_form,
        'user_obj': user,
    }
    
    return render(request, 'accounts/user_update.html', context)


@login_required
@user_passes_test(is_admin)
def user_toggle_active_view(request, user_id):
    """Activer/désactiver un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    status = 'activé' if user.is_active else 'désactivé'
    messages.success(request, f'Utilisateur {user.get_full_name()} {status}.')
    
    return redirect('accounts:user_list')


@login_required
@user_passes_test(is_admin)
def reset_password_view(request, user_id):
    """Réinitialiser le mot de passe d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    temp_password = settings.DEFAULT_TEMP_PASSWORD
    user.set_password(temp_password)
    user.must_change_password = True
    user.save()
    
    messages.success(
        request,
        f'Mot de passe réinitialisé pour {user.get_full_name()}. '
        f'Nouveau mot de passe temporaire: {temp_password}'
    )
    
    return redirect('accounts:user_list')








# === Liste des professeurs ===
@login_required
@user_passes_test(is_admin)
def professor_list_view(request):
    """Liste de tous les professeurs"""
    professors = User.objects.filter(role='PROFESSOR').order_by('last_name', 'first_name')

    search = request.GET.get('search')
    if search:
        professors = professors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    paginator = Paginator(professors, getattr(settings, 'PAGINATION_PER_PAGE', 10))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboards/liste_professeurs.html', {'page_obj': page_obj, 'search': search})


# === Liste des étudiants ===
@login_required
@user_passes_test(is_admin)
def student_list_view(request):
    """Liste de tous les étudiants"""
    students = User.objects.filter(role='STUDENT').order_by('last_name', 'first_name')

    search = request.GET.get('search')
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_profile__student_number__icontains=search) |
            Q(email__icontains=search)
        )

    paginator = Paginator(students, getattr(settings, 'PAGINATION_PER_PAGE', 10))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboards/liste_etudiants.html', {'page_obj': page_obj, 'search': search})
