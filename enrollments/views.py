from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from .models import Enrollment, EnrollmentHistory
from courses.models import CourseSection
from django.db.models import Count, Q, F
from departments.models import Department
from grades.views import is_student, is_professor, is_admin






@login_required
@user_passes_test(is_student)
def available_sections_view(request):
    """Liste les sections disponibles pour l'inscription de l'étudiant connecté."""
    student = request.user.student_profile  # profil étudiant relié à l'utilisateur

    # 🔹 Base : sections ouvertes correspondant au niveau + département de l’étudiant
    sections = CourseSection.objects.filter(
        is_open=True,
        course__year_level=student.current_year,            # même niveau d’étude
        course__department=student.department               # même département
    ).select_related('course', 'professor__user')

    # 🔹 Exclure les cours déjà suivis ou en cours d’inscription
    enrolled_course_ids = student.enrollments.filter(
        status='ENROLLED'
    ).values_list('course_section__course_id', flat=True)
    sections = sections.exclude(course_id__in=enrolled_course_ids)

    # 🔹 Filtres facultatifs depuis le formulaire
    session = request.GET.get('session')
    semester = request.GET.get('semester')
    department = request.GET.get('department')

    if session:
        sections = sections.filter(session=session)
    if semester:
        sections = sections.filter(semester=semester)
    if department:
        sections = sections.filter(course__department__code=department)

    # 🔹 Pagination
    paginator = Paginator(sections.order_by('course__code'), settings.PAGINATION_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🔹 Contexte rendu au template
    context = {
        'page_obj': page_obj,
        'session_choices': CourseSection.SESSION_CHOICES,
        'semester_choices': CourseSection.SEMESTER_CHOICES,
        'departments': Department.objects.all(),
    }

    return render(request, 'enrollments/available_sections.html', context)


@login_required
@user_passes_test(is_student)
def enroll_view(request, section_id):
    """Inscription à une section"""
    student = request.user.student_profile
    section = get_object_or_404(CourseSection, id=section_id)

    # Vérifier si l'étudiant est déjà inscrit à ce cours (toutes sections confondues)
    if Enrollment.objects.filter(
        student=student,
        course_section__course=section.course,
        status='ENROLLED'
    ).exists():
        messages.warning(request, f'Vous êtes déjà inscrit au cours {section.course.code}.')
        return redirect('enrollments:my_enrollments')

    # Vérifier si la section est complète ou fermée
    enrolled_count = Enrollment.objects.filter(course_section=section, status='ENROLLED').count()
    if section.max_students and enrolled_count >= section.max_students:
        messages.error(request, f'La section {section.section_number} de {section.course.code} est complète.')
        return redirect('enrollments:available_sections')

    if not section.is_open:
        messages.error(request, f'La section {section.section_number} de {section.course.code} est fermée.')
        return redirect('enrollments:available_sections')

    # Créer l'inscription
    try:
        enrollment = Enrollment(student=student, course_section=section)
        enrollment.save()
        messages.success(
            request,
            f'Inscription réussie à {section.course.code}-{section.section_number}.'
        )
    except ValidationError as e:
        for msg in e.messages:
            messages.error(request, msg)

    return redirect('enrollments:my_enrollments')



@login_required
@user_passes_test(is_student)
def drop_enrollment_view(request, enrollment_id):
    """Abandonner une inscription"""
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user.student_profile
    )
    
    if enrollment.status != 'ENROLLED':
        messages.warning(request, 'Cette inscription ne peut pas être abandonnée.')
        return redirect('enrollments:my_enrollments')
    
    # Créer un historique
    EnrollmentHistory.objects.create(
        enrollment=enrollment,
        previous_status=enrollment.status,
        new_status='DROPPED',
        changed_by=request.user,
        reason='Abandonné par l\'étudiant'
    )
    
    enrollment.status = 'DROPPED'
    enrollment.drop_date = timezone.now()
    enrollment.save()
    
    messages.success(request, 'Inscription abandonnée avec succès.')
    return redirect('enrollments:my_enrollments')


@login_required
@user_passes_test(is_student)
def my_enrollments_view(request):
    """Mes inscriptions"""
    student = request.user.student_profile
    
    # Filtrer par statut
    status = request.GET.get('status', 'ENROLLED')
    
    enrollments = student.enrollments.filter(
        status=status
    ).select_related(
        'course_section__course',
        'course_section__professor__user'
    ).order_by('-enrollment_date')
    
    # Statistiques
    total_enrolled = student.enrollments.filter(status='ENROLLED').count()
    total_completed = student.enrollments.filter(status='COMPLETED').count()
    total_dropped = student.enrollments.filter(status='DROPPED').count()
    
    context = {
        'enrollments': enrollments,
        'current_status': status,
        'status_choices': Enrollment.STATUS_CHOICES,
        'total_enrolled': total_enrolled,
        'total_completed': total_completed,
        'total_dropped': total_dropped,
    }
    
    return render(request, 'enrollments/my_enrollments.html', context)


from collections import defaultdict
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render
from django.conf import settings

@login_required
@user_passes_test(is_admin)
def enrollment_list_view(request):
    """Liste de toutes les inscriptions groupées par étudiant (admin)"""
    enrollments = Enrollment.objects.select_related(
        'student__user',
        'course_section__course',
        'course_section__professor__user'
    )
    
    # Filtres
    status = request.GET.get('status')
    session = request.GET.get('session')
    semester = request.GET.get('semester')
    student_number = request.GET.get('student_number')
    
    if status:
        enrollments = enrollments.filter(status=status)
    if session:
        enrollments = enrollments.filter(course_section__session=session)
    if semester:
        enrollments = enrollments.filter(course_section__semester=semester)
    if student_number:
        enrollments = enrollments.filter(
            student__student_number__icontains=student_number
        )
    
    # Ordonner par étudiant puis par date
    enrollments = enrollments.order_by('student__student_number', '-enrollment_date')
    
    # Regrouper les inscriptions par étudiant
    grouped_enrollments = defaultdict(list)
    for enrollment in enrollments:
        grouped_enrollments[enrollment.student].append(enrollment)
    
    # Convertir en liste de tuples pour la pagination (student, enrollments_list)
    grouped_list = sorted(
        grouped_enrollments.items(),
        key=lambda x: x[0].student_number
    )
    
    # Pagination sur les étudiants (pas sur les inscriptions)
    paginator = Paginator(grouped_list, settings.PAGINATION_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Convertir page_obj en dictionnaire pour le template
    grouped_dict = dict(page_obj.object_list)
    
    context = {
        'page_obj': page_obj,
        'grouped_enrollments': grouped_dict,
        'status_choices': Enrollment.STATUS_CHOICES,
    }
    
    return render(request, 'enrollments/enrollment_list.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_update_status_view(request, enrollment_id):
    """Modifier le statut d'une inscription (admin)"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        reason = request.POST.get('reason', '')
        
        if new_status and new_status in dict(Enrollment.STATUS_CHOICES):
            # Créer un historique
            EnrollmentHistory.objects.create(
                enrollment=enrollment,
                previous_status=enrollment.status,
                new_status=new_status,
                changed_by=request.user,
                reason=reason
            )
            
            enrollment.status = new_status
            if new_status == 'DROPPED':
                enrollment.drop_date = timezone.now()
            enrollment.save()
            
            messages.success(request, 'Statut d\'inscription modifié.')
        else:
            messages.error(request, 'Statut invalide.')
    
    return redirect('enrollments:enrollment_list')


@login_required
def enrollment_history_view(request, enrollment_id):
    """Historique d'une inscription"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    # Vérifier les permissions
    can_view = (
        request.user.is_admin_user() or
        (request.user.is_student() and 
         enrollment.student == request.user.student_profile)
    )
    
    if not can_view:
        messages.error(request, 'Vous n\'avez pas la permission de voir cet historique.')
        return redirect('home')
    
    history = enrollment.history.select_related('changed_by').order_by('-changed_at')
    
    context = {
        'enrollment': enrollment,
        'history': history,
    }
    
    return render(request, 'enrollments/enrollment_history.html', context)