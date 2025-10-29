from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.conf import settings
from .models import Grade, GradeHistory, Transcript
from enrollments.models import Enrollment
from courses.models import CourseSection
from .forms import GradeForm
from utils.roles import is_admin, is_professor, is_student
from accounts.models import User,Student
from departments.models import Department




@login_required
@user_passes_test(is_professor)
def professor_sections_view(request):
    """Sections du professeur pour la saisie des notes"""
    professor = request.user.professor_profile
    sections = professor.course_sections.select_related('course').annotate(
        enrolled_count=Count('enrollments', filter=Q(enrollments__status='ENROLLED'))
    )
    
    context = {'sections': sections}
    return render(request, 'grades/professor_sections.html', context)


@login_required
@user_passes_test(is_professor)
def grade_entry_view(request, section_id):
    """Saisie des notes pour une section"""
    professor = request.user.professor_profile
    section = get_object_or_404(
        CourseSection,
        id=section_id,
        professor=professor
    )
    
    # Récupérer tous les étudiants inscrits
    enrollments = section.enrollments.filter(
        status='ENROLLED'
    ).select_related('student__user').order_by('student__student_number')
    
    if request.method == 'POST':
        # Traiter les notes soumises
        for enrollment in enrollments:
            grade, created = Grade.objects.get_or_create(
                enrollment=enrollment,
                defaults={'graded_by': professor}
            )
            
            # Sauvegarder l'ancienne valeur pour l'historique
            old_values = {
                'midterm_exam': grade.midterm_exam,
                'final_exam': grade.final_exam,
                'assignments': grade.assignments,
                'participation': grade.participation,
                'project': grade.project,
            }
            
            # Mettre à jour les notes
            components = ['midterm_exam', 'final_exam', 'assignments', 'participation', 'project']
            for component in components:
                field_name = f'grade_{enrollment.id}_{component}'
                value = request.POST.get(field_name)
                if value:
                    try:
                        new_value = float(value)
                        old_value = old_values[component]
                        
                        # Créer un historique si la valeur a changé
                        if old_value != new_value:
                            GradeHistory.objects.create(
                                grade=grade,
                                component=component,
                                old_value=old_value,
                                new_value=new_value,
                                modified_by=professor
                            )
                        
                        setattr(grade, component, new_value)
                    except ValueError:
                        pass
            
            # Commentaires
            comments = request.POST.get(f'comments_{enrollment.id}')
            if comments:
                grade.comments = comments
            
            grade.graded_by = professor
            grade.save()
        
        messages.success(request, 'Notes enregistrées avec succès.')
        return redirect('grades:professor_sections')
    
    # Préparer les données pour l'affichage
    enrollment_grades = []
    for enrollment in enrollments:
        try:
            grade = enrollment.grade
        except Grade.DoesNotExist:
            grade = None
        
        enrollment_grades.append({
            'enrollment': enrollment,
            'grade': grade
        })
    
    context = {
        'section': section,
        'enrollment_grades': enrollment_grades,
    }
    
    return render(request, 'grades/grade_entry.html', context)


@login_required
@user_passes_test(is_student)
def my_grades_view(request):
    """Mes notes (étudiant)"""
    student = request.user.student_profile
    
    # Récupérer toutes les inscriptions avec notes
    enrollments = student.enrollments.filter(
        status__in=['ENROLLED', 'COMPLETED']
    ).select_related(
        'course_section__course',
        'course_section__professor__user'
    ).order_by('-enrollment_date')
    
    # Préparer les données
    enrollment_grades = []
    total_points = 0
    total_credits = 0
    
    for enrollment in enrollments:
        try:
            grade = enrollment.grade
            if grade.final_grade:
                credits = enrollment.course_section.course.credits
                total_points += float(grade.final_grade) * credits
                total_credits += credits
        except Grade.DoesNotExist:
            grade = None
        
        enrollment_grades.append({
            'enrollment': enrollment,
            'grade': grade
        })
    
    # Calculer la moyenne générale
    gpa = round(total_points / total_credits, 2) if total_credits > 0 else None
    
    context = {
        'enrollment_grades': enrollment_grades,
        'gpa': gpa,
        'total_credits': total_credits,
    }
    
    return render(request, 'grades/my_grades.html', context)


@login_required
def grade_detail_view(request, grade_id):
    """Détail d'une note"""
    grade = get_object_or_404(Grade.objects.select_related(
        'enrollment__student__user',
        'enrollment__course_section__course',
        'graded_by__user'
    ), id=grade_id)
    
    # Vérifier les permissions
    can_view = (
        request.user.is_admin_user() or
        (request.user.is_student() and 
         grade.enrollment.student == request.user.student_profile) or
        (request.user.is_professor() and 
         grade.enrollment.course_section.professor == request.user.professor_profile)
    )
    
    if not can_view:
        messages.error(request, 'Vous n\'avez pas la permission de voir cette note.')
        return redirect('home')
    
    # Historique des modifications
    history = grade.history.select_related('modified_by__user').order_by('-modified_at')
    
    context = {
        'grade': grade,
        'history': history,
    }
    
    return render(request, 'grades/grade_detail.html', context)


@login_required
@user_passes_test(is_admin)
def grade_list_view(request):
    """Liste de toutes les notes (admin)"""
    grades = Grade.objects.select_related(
        'enrollment__student__user',
        'enrollment__course_section__course',
        'graded_by__user'
    )
    
    # Filtres
    student_number = request.GET.get('student_number')
    course_code = request.GET.get('course_code')
    min_grade = request.GET.get('min_grade')
    max_grade = request.GET.get('max_grade')
    
    if student_number:
        grades = grades.filter(
            enrollment__student__student_number__icontains=student_number
        )
    
    if course_code:
        grades = grades.filter(
            enrollment__course_section__course__code__icontains=course_code
        )
    
    if min_grade:
        try:
            grades = grades.filter(final_grade__gte=float(min_grade))
        except ValueError:
            pass
    
    if max_grade:
        try:
            grades = grades.filter(final_grade__lte=float(max_grade))
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(grades, settings.PAGINATION_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    
    return render(request, 'grades/grade_list.html', context)

@login_required
@user_passes_test(is_student)
def my_professors_view(request):
    """Affiche les professeurs des cours de l'étudiant connecté"""
    student = request.user.student_profile

    # Récupérer toutes les inscriptions actives de l'étudiant
    enrollments = student.enrollments.filter(
        status__in=['ENROLLED', 'COMPLETED']
    ).select_related(
        'course_section__course',
        'course_section__professor__user'
    )

    # Utiliser un set pour éviter les doublons
    professors = set()
    for enrollment in enrollments:
        professor = getattr(enrollment.course_section.professor, 'user', None)
        if professor:
            professors.add(professor)

    context = {
        'professors': professors,
        'enrollments': enrollments,
    }

    return render(request, 'grades/my_professors.html', context)




@login_required
@user_passes_test(is_student)
def transcript_view(request):
    """Relevé de notes de l'étudiant"""
    student = request.user.student_profile
    
    # Grouper par semestre et année
    from django.db.models import F
    from collections import defaultdict
    
    enrollments = student.enrollments.filter(
        status='COMPLETED'
    ).select_related(
        'course_section__course',
        'grade'
    ).order_by(
        '-course_section__year',
        'course_section__semester'
    )
    
    # Organiser par période académique
    periods = defaultdict(list)
    cumulative_gpa_data = []
    cumulative_credits = 0
    cumulative_points = 0
    
    for enrollment in enrollments:
        period_key = (
            enrollment.course_section.year,
            enrollment.course_section.semester
        )
        
        try:
            grade = enrollment.grade
            if grade.final_grade:
                periods[period_key].append({
                    'enrollment': enrollment,
                    'grade': grade
                })
                
                # Calculer GPA cumulatif
                credits = enrollment.course_section.course.credits
                grade_value = float(grade.final_grade)
                
                # Convertir en points GPA
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
                
                cumulative_points += points * credits
                cumulative_credits += credits
        except Grade.DoesNotExist:
            pass
    
    # Calculer GPA final
    final_gpa = round(cumulative_points / cumulative_credits, 2) if cumulative_credits > 0 else 0
    
    # Trier les périodes
    sorted_periods = sorted(periods.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True)
    
    context = {
        'student': student,
        'periods': sorted_periods,
        'cumulative_credits': cumulative_credits,
        'final_gpa': final_gpa,
    }
    
    return render(request, 'grades/transcript.html', context)


@login_required
@user_passes_test(is_admin)
def generate_transcript_view(request, student_id):
    """Générer un relevé de notes pour un étudiant (admin)"""
    from accounts.models import Student
    student = get_object_or_404(Student, id=student_id)
    
    # Logique similaire à transcript_view mais pour n'importe quel étudiant
    enrollments = student.enrollments.filter(
        status='COMPLETED'
    ).select_related(
        'course_section__course',
        'grade'
    ).order_by(
        '-course_section__year',
        'course_section__semester'
    )
    
    from collections import defaultdict
    periods = defaultdict(list)
    cumulative_credits = 0
    cumulative_points = 0
    
    for enrollment in enrollments:
        period_key = (
            enrollment.course_section.year,
            enrollment.course_section.semester
        )
        
        try:
            grade = enrollment.grade
            if grade.final_grade:
                periods[period_key].append({
                    'enrollment': enrollment,
                    'grade': grade
                })
                
                credits = enrollment.course_section.course.credits
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
                
                cumulative_points += points * credits
                cumulative_credits += credits
        except Grade.DoesNotExist:
            pass
    
    final_gpa = round(cumulative_points / cumulative_credits, 2) if cumulative_credits > 0 else 0
    sorted_periods = sorted(periods.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True)
    
    context = {
        'student': student,
        'periods': sorted_periods,
        'cumulative_credits': cumulative_credits,
        'final_gpa': final_gpa,
    }
    
    return render(request, 'grades/transcript.html', context)


@login_required
def course_statistics_view(request, section_id):
    """Statistiques d'un cours"""
    section = get_object_or_404(CourseSection, id=section_id)
    
    # --- Vérification des permissions ---
    can_view = (
        request.user.is_admin_user() or
        (request.user.is_professor() and 
         section.professor == request.user.professor_profile)
    )
    
    if not can_view:
        messages.error(request, "Vous n'avez pas la permission de voir ces statistiques.")
        return redirect('home')
    
    # --- Récupération des notes valides ---
    grades = Grade.objects.filter(
        enrollment__course_section=section,
        enrollment__status='ENROLLED',
        final_grade__isnull=False
    )
    
    # --- Statistiques générales ---
    stats = grades.aggregate(
        average=Avg('final_grade'),
        count=Count('id')
    )
    
    # --- Distribution des notes ---
    distribution = {
        'A': grades.filter(letter_grade='A').count(),
        'B': grades.filter(letter_grade='B').count(),
        'C': grades.filter(letter_grade='C').count(),
        'D': grades.filter(letter_grade='D').count(),
        'F': grades.filter(letter_grade='F').count(),
    }
    
    # --- Calcul du taux de réussite ---
    total = stats['count'] or 0
    success_count = distribution['A'] + distribution['B'] + distribution['C'] + distribution['D']
    success_rate = round((success_count * 100 / total), 0) if total > 0 else None

    context = {
        'section': section,
        'stats': stats,
        'distribution': distribution,
        'success_rate': success_rate,
    }
    
    return render(request, 'grades/course_statistics.html', context)








@login_required
@user_passes_test(is_professor)
def grades_summary_view(request, section_id):
    """Récapitulatif de toutes les notes d'une section (en lecture seule)"""
    professor = request.user.professor_profile
    section = get_object_or_404(
        CourseSection,
        id=section_id,
        professor=professor
    )
    
    # Récupérer tous les étudiants avec leurs notes
    enrollments = section.enrollments.filter(
        status='ENROLLED'
    ).select_related('student__user').order_by('student__student_number')
    
    enrollment_grades = []
    for enrollment in enrollments:
        try:
            grade = enrollment.grade
        except Grade.DoesNotExist:
            grade = None
        
        enrollment_grades.append({
            'enrollment': enrollment,
            'grade': grade
        })
    
    context = {
        'section': section,
        'enrollment_grades': enrollment_grades,
    }
    
    return render(request, 'grades/grades_summary.html', context)









# ========== grades/views.py - AJOUTER ces vues ==========

@login_required
@user_passes_test(is_professor)
def my_students_view(request):
    """Liste de tous les étudiants du professeur"""
    professor = request.user.professor_profile
    
    # Récupérer toutes les sections du professeur
    sections = professor.course_sections.all()
    
    # Récupérer tous les étudiants inscrits
    enrollments = Enrollment.objects.filter(
        course_section__in=sections,
        status='ENROLLED'
    ).select_related('student__user', 'course_section__course').distinct()
    
    # Organiser par étudiant
    from collections import defaultdict
    students_data = defaultdict(lambda: {
        'student': None,
        'courses': [],
        'total_credits': 0,
        'grades_count': 0,
        'total_points': 0,
        'gpa': 0
    })
    
    for enrollment in enrollments:
        student = enrollment.student
        student_key = student.id
        
        if students_data[student_key]['student'] is None:
            students_data[student_key]['student'] = student
        
        # Ajouter le cours
        students_data[student_key]['courses'].append({
            'course': enrollment.course_section.course,
            'section': enrollment.course_section,
            'enrollment': enrollment
        })
        
        # Calculer le GPA si la note existe
        try:
            grade = enrollment.grade
            if grade.final_grade:
                credits = enrollment.course_section.course.credits
                students_data[student_key]['total_credits'] += credits
                students_data[student_key]['grades_count'] += 1
                
                # Convertir en points
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
                
                students_data[student_key]['total_points'] += points * credits
        except:
            pass
    
    # Calculer le GPA pour chaque étudiant
    for student_id in students_data:
        data = students_data[student_id]
        if data['total_credits'] > 0:
            data['gpa'] = round(data['total_points'] / data['total_credits'], 2)
    
    # Convertir en liste
    students_list = list(students_data.values())
    
    # Filtres
    search = request.GET.get('search', '')
    if search:
        students_list = [
            s for s in students_list 
            if search.lower() in s['student'].user.get_full_name().lower() or
               search.lower() in s['student'].student_number.lower()
        ]
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(students_list, settings.PAGINATION_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search,
        'total_students': len(students_list),
    }
    
    return render(request, 'grades/my_students.html', context)


@login_required
@user_passes_test(is_professor)
def palmares_view(request):
    """Palmarès des étudiants du professeur"""
    professor = request.user.professor_profile
    
    # Filtres
    section_id = request.GET.get('section')
    semester = request.GET.get('semester', '')
    year = request.GET.get('year', '')
    
    # Récupérer les sections du professeur
    sections = professor.course_sections.all()
    
    if section_id:
        sections = sections.filter(id=section_id)
    if semester:
        sections = sections.filter(semester=semester)
    if year:
        sections = sections.filter(year=year)
    
    # Récupérer tous les étudiants avec leurs notes
    from collections import defaultdict
    students_data = defaultdict(lambda: {
        'student': None,
        'courses': [],
        'total_points': 0,
        'total_credits': 0,
        'gpa': 0,
        'grades': []
    })
    
    enrollments = Enrollment.objects.filter(
        course_section__in=sections,
        status__in=['ENROLLED', 'COMPLETED']
    ).select_related(
        'student__user',
        'course_section__course'
    ).prefetch_related('grade')
    
    for enrollment in enrollments:
        student = enrollment.student
        student_key = student.id
        
        if students_data[student_key]['student'] is None:
            students_data[student_key]['student'] = student
        
        try:
            grade = enrollment.grade
            if grade.final_grade:
                credits = enrollment.course_section.course.credits
                grade_value = float(grade.final_grade)
                
                # Convertir en points GPA
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
                
                students_data[student_key]['total_points'] += points * credits
                students_data[student_key]['total_credits'] += credits
                students_data[student_key]['courses'].append(enrollment.course_section.course.code)
                students_data[student_key]['grades'].append({
                    'course': enrollment.course_section.course,
                    'grade': grade.final_grade,
                    'letter': grade.letter_grade
                })
        except:
            pass
    
    # Calculer le GPA et créer la liste
    palmares_list = []
    for student_id, data in students_data.items():
        if data['total_credits'] > 0:
            data['gpa'] = round(data['total_points'] / data['total_credits'], 2)
            palmares_list.append(data)
    
    # Trier par GPA décroissant
    palmares_list.sort(key=lambda x: x['gpa'], reverse=True)
    
    # Ajouter le rang
    for index, student_data in enumerate(palmares_list, start=1):
        student_data['rank'] = index
        
        # Déterminer la mention
        gpa = student_data['gpa']
        if gpa >= 3.7:
            student_data['mention'] = 'Summa Cum Laude'
            student_data['mention_class'] = 'success'
        elif gpa >= 3.3:
            student_data['mention'] = 'Magna Cum Laude'
            student_data['mention_class'] = 'info'
        elif gpa >= 3.0:
            student_data['mention'] = 'Cum Laude'
            student_data['mention_class'] = 'primary'
        else:
            student_data['mention'] = 'Passable'
            student_data['mention_class'] = 'secondary'
    
    # Filtrer par recherche
    search = request.GET.get('search', '')
    if search:
        palmares_list = [
            s for s in palmares_list
            if search.lower() in s['student'].user.get_full_name().lower() or
               search.lower() in s['student'].student_number.lower()
        ]
    
    # Statistiques
    if palmares_list:
        avg_gpa = sum(s['gpa'] for s in palmares_list) / len(palmares_list)
        top_student = palmares_list[0] if palmares_list else None
    else:
        avg_gpa = 0
        top_student = None
    
    context = {
        'palmares_list': palmares_list,
        'sections': professor.course_sections.all(),
        'selected_section': section_id,
        'search_query': search,
        'semester': semester,
        'year': year,
        'total_students': len(palmares_list),
        'avg_gpa': round(avg_gpa, 2) if avg_gpa else 0,
        'top_student': top_student,
        'semester_choices': CourseSection.SEMESTER_CHOICES,
    }
    
    return render(request, 'grades/palmares.html', context)








@login_required
@user_passes_test(is_admin)
def students_gpa_view(request):
    """Vue pour afficher le GPA de tous les étudiants avec filtres"""
    
    department = request.GET.get('department')
    year = request.GET.get('year')

    # Base : tous les étudiants actifs
    students = User.objects.filter(role='STUDENT', is_active=True)
    
    if department:
        students = students.filter(student_profile__department__code=department)
    if year:
        students = students.filter(student_profile__current_year=year)
    
    students_gpa = []

    for student in students.select_related('student_profile__department'):
        enrollments = student.student_profile.enrollments.filter(
            status__in=['ENROLLED', 'COMPLETED']
        ).select_related('course_section__course')

        total_points = 0
        total_credits = 0

        for enrollment in enrollments:
            try:
                grade = enrollment.grade
                if grade.final_grade is not None:
                    credits = enrollment.course_section.course.credits
                    total_points += float(grade.final_grade) * credits
                    total_credits += credits
            except Grade.DoesNotExist:
                continue

        gpa = round(total_points / total_credits, 2) if total_credits > 0 else None

        students_gpa.append({
            'student': student,
            'department': student.student_profile.department.name if student.student_profile.department else '-',
            'year': student.student_profile.get_current_year_display(),
            'gpa': gpa,
            'total_credits': total_credits,
            'courses_count': enrollments.count()
        })

    # Pagination
    paginator = Paginator(students_gpa, getattr(settings, 'PAGINATION_PER_PAGE', 20))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Données pour les filtres
    departments = Department.objects.values_list('code', 'name')
    years = Student.YEAR_CHOICES

    context = {
        'page_obj': page_obj,
        'departments': departments,
        'years': years,
        'selected_department': department,
        'selected_year': year,
    }

    return render(request, 'grades/students_gpa.html', context)
