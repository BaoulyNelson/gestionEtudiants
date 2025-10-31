from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings
from .models import Course, CourseSection
from .forms import CourseForm, CourseSectionForm
from accounts.views import is_admin

@login_required
def course_list_view(request):
    """Liste des cours"""
    courses = Course.objects.filter(is_active=True).select_related('department')

    # Filtres
    department = request.GET.get('department')
    year_level = request.GET.get('year_level')
    search = request.GET.get('search')

    # --- Logique de filtrage ---
    if year_level:
        courses = courses.filter(year_level=year_level)

        # Si c'est l'année préparatoire (1), on ignore tout filtre de département
        if year_level == "1":
            courses = courses.filter(department__isnull=True)
        elif department:
            courses = courses.filter(department__code=department)
    elif department:
        courses = courses.filter(department__code=department)

    if search:
        courses = courses.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search)
        )

    # Pagination
    paginator = Paginator(courses, settings.PAGINATION_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    from departments.models import Department

    context = {
        'page_obj': page_obj,
        'departments': Department.objects.all(),
        'year_choices': Course.YEAR_CHOICES,
        'current_department': department,
        'current_year': year_level,
        'search_query': search,
    }

    return render(request, 'courses/course_list.html', context)


@login_required
def course_detail_view(request, course_id):
    """Détails d'un cours"""
    course = get_object_or_404(Course, id=course_id)
    sections = course.sections.select_related('professor__user').order_by('section_number')
    
    # Si l'utilisateur est un étudiant, afficher seulement ses sections
    if request.user.is_student():
        student = request.user.student_profile
        enrolled_sections = sections.filter(
            enrollments__student=student,
            enrollments__status='ENROLLED'
        )
        sections = enrolled_sections if enrolled_sections.exists() else sections
    
    context = {
        'course': course,
        'sections': sections,
    }
    
    return render(request, 'courses/course_detail.html', context)


@login_required
@user_passes_test(is_admin)
def course_create_view(request):
    """Créer un nouveau cours"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Cours {course.code} créé avec succès.')
            return redirect('courses:course_list')
    else:
        form = CourseForm()
    
    return render(request, 'courses/course_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def course_update_view(request, course_id):
    """Modifier un cours"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cours modifié avec succès.')
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'course': course
    })


@login_required
@user_passes_test(is_admin)
def course_delete_view(request, course_id):
    """Désactiver un cours"""
    course = get_object_or_404(Course, id=course_id)
    course.is_active = False
    course.save()
    messages.success(request, f'Cours {course.code} désactivé.')
    return redirect('courses:course_list')


# Vues pour les sections de cours

@login_required
def section_list_view(request):
    """Liste des sections de cours"""
    sections = CourseSection.objects.select_related(
        'course', 'professor__user'
    ).annotate(
        enrolled_count=Count('enrollments', filter=Q(enrollments__status='ENROLLED'))
    )
    
    # Filtres
    session = request.GET.get('session')
    semester = request.GET.get('semester')
    year = request.GET.get('year')
    professor = request.GET.get('professor')
    
    if session:
        sections = sections.filter(session=session)
    
    if semester:
        sections = sections.filter(semester=semester)
    
    if year:
        sections = sections.filter(year=year)
    
    if professor:
        sections = sections.filter(professor_id=professor)
    
    # Si l'utilisateur est un professeur, afficher seulement ses sections
    if request.user.is_professor():
        sections = sections.filter(professor=request.user.professor_profile)
    
    # ⚡️ Ajout d'un ordre stable pour éviter le warning de pagination
    sections = sections.order_by('year', 'semester', 'session', 'course__code', 'section_number')
    
    # Pagination
    paginator = Paginator(sections, settings.PAGINATION_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'session_choices': CourseSection.SESSION_CHOICES,
        'semester_choices': CourseSection.SEMESTER_CHOICES,
    }
    
    return render(request, 'courses/section_list.html', context)


@login_required
def section_detail_view(request, section_id):
    """Détails d'une section de cours"""
    section = get_object_or_404(
        CourseSection.objects.select_related('course', 'professor__user'),
        id=section_id
    )
    
    # Liste des étudiants inscrits
    enrollments = section.enrollments.filter(
        status='ENROLLED'
    ).select_related('student__user')
    
    # Vérifier les permissions
    can_view_students = (
        request.user.is_admin_user() or
        (request.user.is_professor() and 
         section.professor == request.user.professor_profile)
    )
    
    context = {
        'section': section,
        'enrollments': enrollments if can_view_students else None,
        'can_view_students': can_view_students,
    }
    
    return render(request, 'courses/section_detail.html', context)


@login_required
@user_passes_test(is_admin)
def section_create_view(request, course_id=None):
    """Créer une nouvelle section de cours"""
    course = None
    if course_id:
        course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            section = form.save()
            messages.success(
                request, 
                f'Section {section.course.code}-{section.section_number} créée.'
            )
            return redirect('courses:section_detail', section_id=section.id)
    else:
        initial = {'course': course} if course else {}
        form = CourseSectionForm(initial=initial)
    
    return render(request, 'courses/section_form.html', {
        'form': form,
        'course': course
    })


@login_required
@user_passes_test(is_admin)
def section_update_view(request, section_id):
    """Modifier une section de cours"""
    section = get_object_or_404(CourseSection, id=section_id)
    
    if request.method == 'POST':
        form = CourseSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section modifiée avec succès.')
            return redirect('courses:section_detail', section_id=section.id)
    else:
        form = CourseSectionForm(instance=section)
    
    return render(request, 'courses/section_form.html', {
        'form': form,
        'section': section
    })

@login_required
@user_passes_test(is_admin)
def section_delete_view(request, pk):
    """Permet à un admin de supprimer une section"""
    section = get_object_or_404(CourseSection, pk=pk)

    if request.method == "POST":
        course_id = section.course.id  # Pour rediriger après suppression
        section.delete()
        messages.success(request, f"La section {section} a été supprimée avec succès.")
        return redirect('courses:course_detail', pk=course_id)

    return render(request, 'courses/section_confirm_delete.html', {'section': section})


@login_required
@user_passes_test(is_admin)
def section_toggle_open_view(request, section_id):
    """Ouvrir/fermer une section aux inscriptions"""
    section = get_object_or_404(CourseSection, id=section_id)
    section.is_open = not section.is_open
    section.save()
    
    status = 'ouverte' if section.is_open else 'fermée'
    messages.success(request, f'Section {status} aux inscriptions.')
    
    return redirect('courses:section_detail', section_id=section.id)


@login_required 
def my_courses_view(request):
    """Cours de l'utilisateur connecté"""
    if request.user.is_student():
        student = request.user.student_profile
        enrollments = student.enrollments.filter(
            status='ENROLLED'
        ).select_related('course_section__course', 'course_section__professor__user')
        
        context = {
            'enrollments': enrollments,
            'is_student': True,
            'course_count': enrollments.count()  # 👈 Ajout du compteur
        }
        
        return render(request, 'courses/my_courses.html', context)
    
    elif request.user.is_professor():
        professor = request.user.professor_profile
        sections = professor.course_sections.select_related('course').annotate(
            enrolled_count=Count('enrollments', filter=Q(enrollments__status='ENROLLED'))
        )
        
        context = {
            'sections': sections,
            'is_professor': True,
            'course_count': sections.count()  # 👈 facultatif pour prof
        }
        
        return render(request, 'courses/my_courses.html', context)
    
    else:
        messages.warning(request, 'Cette fonctionnalité n\'est disponible que pour les étudiants et professeurs.')
        return redirect('home')
