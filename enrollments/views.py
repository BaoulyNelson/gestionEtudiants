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
from utils.roles import is_student, is_admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.core.paginator import Paginator
from django.conf import settings
from collections import defaultdict
from .models import Enrollment





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


# ========== SOLUTION 1 : Corriger la vue (Recommandé) ==========



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

    # === VÉRIFIER LA LIMITE DE 8 COURS ===
    session_enrollments = Enrollment.objects.filter(
        student=student,
        course_section__session=section.session,
        course_section__semester=section.semester,
        course_section__year=section.year,
        status='ENROLLED'
    ).count()
    
    max_courses = getattr(settings, 'MAX_COURSES_PER_SESSION', 8)
    if session_enrollments >= max_courses:
        messages.error(
            request,
            f'Vous avez atteint le maximum de {max_courses} cours pour cette session. '
            f'Vous êtes actuellement inscrit à {session_enrollments} cours.'
        )
        return redirect('enrollments:available_sections')

    # Vérifier si la section est complète ou fermée
    enrolled_count = Enrollment.objects.filter(course_section=section, status='ENROLLED').count()
    if section.max_students and enrolled_count >= section.max_students:
        messages.error(request, f'La section {section.section_number} de {section.course.code} est complète.')
        return redirect('enrollments:available_sections')

    if not section.is_open:
        messages.error(request, f'La section {section.section_number} de {section.course.code} est fermée.')
        return redirect('enrollments:available_sections')

    # === VÉRIFIER LES CONFLITS D'HORAIRE ===
    conflicting_enrollments = Enrollment.objects.filter(
        student=student,
        course_section__session=section.session,
        course_section__semester=section.semester,
        course_section__year=section.year,
        course_section__day_of_week=section.day_of_week,
        status='ENROLLED'
    )
    
    for enrollment in conflicting_enrollments:
        existing_section = enrollment.course_section
        if existing_section.has_schedule_conflict(
            section.day_of_week,
            section.start_time,
            section.end_time
        ):
            messages.error(
                request,
                f'Conflit d\'horaire avec le cours {existing_section.course.code}-'
                f'{existing_section.section_number} '
                f'({existing_section.get_day_of_week_display()} '
                f'{existing_section.start_time.strftime("%H:%M")}-'
                f'{existing_section.end_time.strftime("%H:%M")}).'
            )
            return redirect('enrollments:available_sections')

    # Créer l'inscription
    try:
        enrollment = Enrollment(student=student, course_section=section)
        # IMPORTANT : Appeler full_clean() pour déclencher clean()
        enrollment.full_clean()
        enrollment.save()
        messages.success(
            request,
            f'✓ Inscription réussie à {section.course.code}-{section.section_number}.'
        )
    except ValidationError as e:
        # Afficher toutes les erreurs de validation
        if hasattr(e, 'message_dict'):
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        else:
            for msg in e.messages:
                messages.error(request, msg)
        return redirect('enrollments:available_sections')
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'inscription : {str(e)}')
        return redirect('enrollments:available_sections')

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







@login_required
@user_passes_test(is_admin)
def enrollment_list_view(request):
    """Liste de toutes les inscriptions groupées par étudiant (admin)"""
    
    # Récupérer toutes les inscriptions avec relations
    enrollments_qs = Enrollment.objects.select_related(
        'student__user',
        'course_section__course',
        'course_section__professor__user'
    )
    
    # Appliquer les filtres
    status = request.GET.get('status', '').strip()
    session = request.GET.get('session', '').strip()
    semester = request.GET.get('semester', '').strip()
    student_number = request.GET.get('student_number', '').strip()
    
    if status:
        enrollments_qs = enrollments_qs.filter(status=status)
    
    if session:
        enrollments_qs = enrollments_qs.filter(course_section__session=session)
    
    if semester:
        enrollments_qs = enrollments_qs.filter(course_section__semester=semester)
    
    if student_number:
        enrollments_qs = enrollments_qs.filter(
            student__student_number__icontains=student_number
        )
    
    # Ordonner par étudiant puis par date (plus récent en premier)
    enrollments_qs = enrollments_qs.order_by(
        'student__student_number',
        '-enrollment_date'
    )
    
    # Convertir en liste pour grouper
    all_enrollments = list(enrollments_qs)
    
    # Grouper par étudiant
    grouped_enrollments = []
    current_student = None
    current_group = []
    
    for enrollment in all_enrollments:
        student_number = enrollment.student.student_number
        
        if current_student != student_number:
            # Sauvegarder le groupe précédent
            if current_group:
                enrolled_count = sum(1 for e in current_group if e.status == 'ENROLLED')
                grouped_enrollments.append({
                    'student': current_group[0].student,
                    'enrollments': current_group,
                    'count': len(current_group),
                    'enrolled_count': enrolled_count
                })
            
            # Nouveau groupe
            current_student = student_number
            current_group = [enrollment]
        else:
            current_group.append(enrollment)
    
    # Ajouter le dernier groupe
    if current_group:
        enrolled_count = sum(1 for e in current_group if e.status == 'ENROLLED')
        grouped_enrollments.append({
            'student': current_group[0].student,
            'enrollments': current_group,
            'count': len(current_group),
            'enrolled_count': enrolled_count
        })
    
    # Statistiques
    total_students = len(grouped_enrollments)
    total_enrollments = len(all_enrollments)
    avg_enrollments = total_enrollments / total_students if total_students > 0 else 0
    
    # Pagination (par étudiant, pas par inscription)
    per_page = getattr(settings, 'PAGINATION_PER_PAGE', 20)
    paginator = Paginator(grouped_enrollments, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'grouped_enrollments': page_obj.object_list,
        'page_obj': page_obj,
        'status_choices': Enrollment.STATUS_CHOICES,
        'total_students': total_students,
        'total_enrollments': total_enrollments,
        'avg_enrollments': avg_enrollments,
    }
    
    return render(request, 'enrollments/enrollment_list.html', context)


# ========== VERSION ALTERNATIVE AVEC DICTIONNAIRE ==========

# ========== VERSION ULTRA-OPTIMISÉE AVEC ANNOTATE ==========



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







# ========== Ajouter ces vues dans enrollments/views.py ==========

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Enrollment, EnrollmentHistory
from courses.models import CourseSection
from accounts.models import Student
from utils.roles import is_admin


@login_required
@user_passes_test(is_admin)
def enrollment_create_view(request):
    """Créer une nouvelle inscription (admin/superuser)"""
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        section_id = request.POST.get('section')
        
        if not student_id or not section_id:
            messages.error(request, 'Veuillez sélectionner un étudiant et une section.')
            return redirect('enrollments:enrollment_create')
        
        try:
            student = Student.objects.get(id=student_id)
            section = CourseSection.objects.get(id=section_id)
            
            # Vérifier si l'étudiant est déjà inscrit à ce cours
            if Enrollment.objects.filter(
                student=student,
                course_section__course=section.course,
                status='ENROLLED'
            ).exists():
                messages.warning(
                    request, 
                    f'L\'étudiant {student.student_number} est déjà inscrit au cours {section.course.code}.'
                )
                return redirect('enrollments:enrollment_create')
            
            # Vérifier la limite de 8 cours
            session_enrollments = Enrollment.objects.filter(
                student=student,
                course_section__session=section.session,
                course_section__semester=section.semester,
                course_section__year=section.year,
                status='ENROLLED'
            ).count()
            
            from django.conf import settings
            max_courses = getattr(settings, 'MAX_COURSES_PER_SESSION', 8)
            if session_enrollments >= max_courses:
                messages.error(
                    request,
                    f'L\'étudiant a atteint le maximum de {max_courses} cours pour cette session. '
                    f'Actuellement inscrit à {session_enrollments} cours.'
                )
                return redirect('enrollments:enrollment_create')
            
            # Vérifier si la section est complète
            enrolled_count = Enrollment.objects.filter(
                course_section=section, 
                status='ENROLLED'
            ).count()
            
            if section.max_students and enrolled_count >= section.max_students:
                messages.error(
                    request, 
                    f'La section {section.section_number} de {section.course.code} est complète.'
                )
                return redirect('enrollments:enrollment_create')
            
            # Vérifier les conflits d'horaire
            conflicting_enrollments = Enrollment.objects.filter(
                student=student,
                course_section__session=section.session,
                course_section__semester=section.semester,
                course_section__year=section.year,
                course_section__day_of_week=section.day_of_week,
                status='ENROLLED'
            )
            
            for enrollment in conflicting_enrollments:
                existing_section = enrollment.course_section
                if existing_section.has_schedule_conflict(
                    section.day_of_week,
                    section.start_time,
                    section.end_time
                ):
                    messages.error(
                        request,
                        f'Conflit d\'horaire avec le cours {existing_section.course.code}-'
                        f'{existing_section.section_number} '
                        f'({existing_section.get_day_of_week_display()} '
                        f'{existing_section.start_time.strftime("%H:%M")}-'
                        f'{existing_section.end_time.strftime("%H:%M")}).'
                    )
                    return redirect('enrollments:enrollment_create')
            
            # Créer l'inscription
            enrollment = Enrollment(student=student, course_section=section)
            enrollment.full_clean()
            enrollment.save()
            
            # Créer un historique
            EnrollmentHistory.objects.create(
                enrollment=enrollment,
                previous_status='',
                new_status='ENROLLED',
                changed_by=request.user,
                reason=f'Inscription créée par {request.user.get_full_name()}'
            )
            
            messages.success(
                request,
                f'✓ Inscription créée avec succès pour {student.user.get_full_name()} '
                f'au cours {section.course.code}-{section.section_number}.'
            )
            return redirect('enrollments:enrollment_list')
            
        except Student.DoesNotExist:
            messages.error(request, 'Étudiant introuvable.')
        except CourseSection.DoesNotExist:
            messages.error(request, 'Section introuvable.')
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            else:
                for msg in e.messages:
                    messages.error(request, msg)
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
        
        return redirect('enrollments:enrollment_create')
    
    # GET request - Afficher le formulaire
    # Récupérer les étudiants actifs
    students = Student.objects.filter(
        user__is_active=True
    ).select_related('user', 'department').order_by('student_number')
    
    # Récupérer les sections ouvertes
    sections = CourseSection.objects.filter(
        is_open=True
    ).select_related(
        'course',
        'professor__user'
    ).order_by('course__code', 'section_number')
    
    # Grouper les sections par cours pour un meilleur affichage
    from collections import defaultdict
    sections_by_course = defaultdict(list)
    for section in sections:
        sections_by_course[section.course].append(section)
    
    context = {
        'students': students,
        'sections_by_course': dict(sections_by_course),
        'session_choices': CourseSection.SESSION_CHOICES,
        'semester_choices': CourseSection.SEMESTER_CHOICES,
    }
    
    return render(request, 'enrollments/enrollment_create.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_update_view(request, enrollment_id):
    """Modifier une inscription existante (admin/superuser)"""
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            'student__user',
            'course_section__course'
        ),
        id=enrollment_id
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        reason = request.POST.get('reason', '').strip()
        
        if not new_status:
            messages.error(request, 'Veuillez sélectionner un statut.')
            return redirect('enrollments:enrollment_update', enrollment_id=enrollment_id)
        
        if new_status not in dict(Enrollment.STATUS_CHOICES):
            messages.error(request, 'Statut invalide.')
            return redirect('enrollments:enrollment_update', enrollment_id=enrollment_id)
        
        # Si le statut a changé
        if new_status != enrollment.status:
            # Créer un historique
            EnrollmentHistory.objects.create(
                enrollment=enrollment,
                previous_status=enrollment.status,
                new_status=new_status,
                changed_by=request.user,
                reason=reason or f'Modifié par {request.user.get_full_name()}'
            )
            
            # Mettre à jour le statut
            old_status = enrollment.get_status_display()
            enrollment.status = new_status
            
            # Si le nouveau statut est DROPPED, enregistrer la date
            if new_status == 'DROPPED':
                enrollment.drop_date = timezone.now()
            
            enrollment.save()
            
            messages.success(
                request,
                f'Statut modifié de "{old_status}" à "{enrollment.get_status_display()}".'
            )
            return redirect('enrollments:enrollment_list')
        else:
            messages.info(request, 'Aucun changement détecté.')
            return redirect('enrollments:enrollment_update', enrollment_id=enrollment_id)
    
    # GET request - Afficher le formulaire
    context = {
        'enrollment': enrollment,
        'status_choices': Enrollment.STATUS_CHOICES,
    }
    
    return render(request, 'enrollments/enrollment_update.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_delete_view(request, enrollment_id):
    """Supprimer une inscription (admin/superuser uniquement)"""
    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            'student__user',
            'course_section__course'
        ),
        id=enrollment_id
    )
    
    if request.method == 'POST':
        student_name = enrollment.student.user.get_full_name()
        course_code = enrollment.course_section.course.code
        section_number = enrollment.course_section.section_number
        
        # Créer un historique avant suppression
        EnrollmentHistory.objects.create(
            enrollment=enrollment,
            previous_status=enrollment.status,
            new_status='DELETED',
            changed_by=request.user,
            reason=f'Inscription supprimée par {request.user.get_full_name()}'
        )
        
        enrollment.delete()
        
        messages.success(
            request,
            f'Inscription supprimée : {student_name} - {course_code}-{section_number}'
        )
        return redirect('enrollments:enrollment_list')
    
    context = {
        'enrollment': enrollment,
    }
    
    return render(request, 'enrollments/enrollment_delete_confirm.html', context)