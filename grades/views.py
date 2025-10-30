import csv
from django.http import HttpResponse, JsonResponse
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
from accounts.models import User, Student
from departments.models import Department
from collections import defaultdict


@login_required
@user_passes_test(is_professor)
def professor_sections_view(request):
    """Sections du professeur pour la saisie des notes"""
    if request.user.is_superuser:
        # Superuser voit toutes les sections
        sections = CourseSection.objects.all().select_related('course', 'professor')
    else:
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
    section = get_object_or_404(CourseSection, id=section_id)
    
    # Vérification des permissions
    if not request.user.is_superuser:
        # Pour les professeurs normaux, vérifier qu'ils enseignent cette section
        if section.professor != request.user.professor_profile:
            messages.error(request, "Vous n'avez pas accès à cette section.")
            return redirect('grades:professor_sections')
    
    # Récupérer tous les étudiants inscrits
    enrollments = section.enrollments.filter(
        status='ENROLLED'
    ).select_related('student__user').order_by('student__student_number')
    
    if request.method == 'POST':
        # Déterminer qui enregistre les notes
        if request.user.is_superuser:
            graded_by = section.professor  # Attribuer au prof de la section
        else:
            graded_by = request.user.professor_profile
        
        # Traiter les notes soumises
        for enrollment in enrollments:
            grade, created = Grade.objects.get_or_create(
                enrollment=enrollment,
                defaults={'graded_by': graded_by}
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
                                modified_by=graded_by
                            )
                        
                        setattr(grade, component, new_value)
                    except ValueError:
                        pass
            
            # Commentaires
            comments = request.POST.get(f'comments_{enrollment.id}')
            if comments:
                grade.comments = comments
            
            grade.graded_by = graded_by
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
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect('home')
    
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
    can_view = request.user.is_superuser or request.user.is_admin_user()
    
    if not can_view and request.user.is_student():
        can_view = (grade.enrollment.student == request.user.student_profile)
    
    if not can_view and request.user.is_professor():
        can_view = (grade.enrollment.course_section.professor == request.user.professor_profile)
    
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
    """Version simple et performante - RECOMMANDÉE"""
    
    # Récupérer toutes les notes avec relations
    grades_qs = Grade.objects.select_related(
        'enrollment__student__user',
        'enrollment__course_section__course',
        'enrollment__course_section__professor__user',
        'graded_by__user'
    )
    
    # Appliquer les filtres
    student_number = request.GET.get('student_number', '').strip()
    course_code = request.GET.get('course_code', '').strip()
    min_grade = request.GET.get('min_grade', '').strip()
    max_grade = request.GET.get('max_grade', '').strip()
    
    if student_number:
        grades_qs = grades_qs.filter(
            enrollment__student__student_number__icontains=student_number
        )
    
    if course_code:
        grades_qs = grades_qs.filter(
            enrollment__course_section__course__code__icontains=course_code
        )
    
    if min_grade:
        try:
            grades_qs = grades_qs.filter(final_grade__gte=float(min_grade))
        except ValueError:
            pass
    
    if max_grade:
        try:
            grades_qs = grades_qs.filter(final_grade__lte=float(max_grade))
        except ValueError:
            pass
    
    # Trier par étudiant puis par cours
    grades_qs = grades_qs.order_by(
        'enrollment__student__student_number',
        'enrollment__course_section__course__code'
    )
    
    # Convertir en liste pour grouper
    all_grades = list(grades_qs)
    
    # Grouper par étudiant
    grouped_grades = []
    current_student = None
    current_group = []
    
    for grade in all_grades:
        student_number = grade.enrollment.student.student_number
        
        if current_student != student_number:
            # Sauvegarder le groupe précédent
            if current_group:
                grouped_grades.append({
                    'student': current_group[0].enrollment.student,
                    'grades': current_group,
                    'count': len(current_group)
                })
            
            # Nouveau groupe
            current_student = student_number
            current_group = [grade]
        else:
            current_group.append(grade)
    
    # Ajouter le dernier groupe
    if current_group:
        grouped_grades.append({
            'student': current_group[0].enrollment.student,
            'grades': current_group,
            'count': len(current_group)
        })
    
    # Pagination
    per_page = getattr(settings, 'PAGINATION_PER_PAGE', 20)
    paginator = Paginator(grouped_grades, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'grouped_grades': page_obj.object_list,
        'page_obj': page_obj,
        'total_students': len(grouped_grades),
        'total_grades': len(all_grades),
    }
    
    return render(request, 'grades/grade_list.html', context)


@login_required
@user_passes_test(is_student)
def my_professors_view(request):
    """Affiche les professeurs des cours de l'étudiant connecté"""
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect('home')
    
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
    if request.user.is_superuser:
        messages.warning(request, "Les superusers n'ont pas de profil étudiant.")
        return redirect('home')
    
    student = request.user.student_profile
    
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
    student = get_object_or_404(Student, id=student_id)
    
    enrollments = student.enrollments.filter(
        status='COMPLETED'
    ).select_related(
        'course_section__course',
        'grade'
    ).order_by(
        '-course_section__year',
        'course_section__semester'
    )
    
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
    
    # Vérification des permissions
    can_view = request.user.is_superuser or request.user.is_admin_user()
    
    if not can_view and request.user.is_professor():
        can_view = (section.professor == request.user.professor_profile)
    
    if not can_view:
        messages.error(request, "Vous n'avez pas la permission de voir ces statistiques.")
        return redirect('home')
    
    # Récupération des notes valides
    grades = Grade.objects.filter(
        enrollment__course_section=section,
        enrollment__status='ENROLLED',
        final_grade__isnull=False
    )
    
    # Statistiques générales
    stats = grades.aggregate(
        average=Avg('final_grade'),
        count=Count('id')
    )
    
    # Distribution des notes
    distribution = {
        'A': grades.filter(letter_grade='A').count(),
        'B': grades.filter(letter_grade='B').count(),
        'C': grades.filter(letter_grade='C').count(),
        'D': grades.filter(letter_grade='D').count(),
        'F': grades.filter(letter_grade='F').count(),
    }
    
    # Calcul du taux de réussite
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
    section = get_object_or_404(CourseSection, id=section_id)
    
    # Vérification des permissions
    if not request.user.is_superuser:
        if section.professor != request.user.professor_profile:
            messages.error(request, "Vous n'avez pas accès à cette section.")
            return redirect('grades:professor_sections')
    
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


@login_required
@user_passes_test(is_professor)
def my_students_view(request):
    """Liste de tous les étudiants du professeur"""
    if request.user.is_superuser:
        # Superuser voit tous les étudiants
        sections = CourseSection.objects.all()
    else:
        professor = request.user.professor_profile
        sections = professor.course_sections.all()
    
    # Récupérer tous les étudiants inscrits
    enrollments = Enrollment.objects.filter(
        course_section__in=sections,
        status='ENROLLED'
    ).select_related('student__user', 'course_section__course').distinct()
    
    # Organiser par étudiant
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
    paginator = Paginator(students_list, getattr(settings, 'PAGINATION_PER_PAGE', 20))
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
    if request.user.is_superuser:
        # Superuser voit toutes les sections
        sections = CourseSection.objects.all()
    else:
        professor = request.user.professor_profile
        sections = professor.course_sections.all()
    
    # Filtres
    section_id = request.GET.get('section')
    semester = request.GET.get('semester', '')
    year = request.GET.get('year', '')
    
    if section_id:
        sections = sections.filter(id=section_id)
    if semester:
        sections = sections.filter(semester=semester)
    if year:
        sections = sections.filter(year=year)
    
    # Récupérer tous les étudiants avec leurs notes
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
    
    # Pour les filtres, afficher toutes les sections accessibles
    if request.user.is_superuser:
        all_sections = CourseSection.objects.all()
    else:
        all_sections = request.user.professor_profile.course_sections.all()
    
    context = {
        'palmares_list': palmares_list,
        'sections': all_sections,
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




















@login_required
@user_passes_test(is_admin)
def grade_edit(request, grade_id):
    """Modifier une note existante"""
    
    grade = get_object_or_404(Grade, id=grade_id)
    
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.graded_by = request.user.professor_profile
            grade.save()
            messages.success(request, 'Note mise à jour avec succès')
            return redirect('grades:admin_grade_list')
    else:
        form = GradeForm(instance=grade)
    
    context = {
        'form': form,
        'grade': grade,
        'action': 'Modifier'
    }
    return render(request, 'grades/grade_form.html', context)


@login_required
@user_passes_test(is_admin)
def grade_delete(request, grade_id):
    """Supprimer une note"""
    
    grade = get_object_or_404(Grade, id=grade_id)
    
    if request.method == 'POST':
        student_name = grade.enrollment.student.user.get_full_name()
        course_code = grade.enrollment.course_section.course.code
        grade.delete()
        messages.success(request, f'Note supprimée pour {student_name} - {course_code}')
        return redirect('grades:admin_grade_list')
    
    context = {'grade': grade}
    return render(request, 'grades/grade_confirm_delete.html', context)


@login_required
@user_passes_test(is_admin)
def grade_bulk_entry(request):
    """Saisie en masse des notes pour une section"""
    
    section_id = request.GET.get('section_id')
    section = None
    enrollments = []
    
    if section_id:
        from courses.models import CourseSection
        section = get_object_or_404(CourseSection, id=section_id)
        
        # Récupérer toutes les inscriptions actives
        enrollments = Enrollment.objects.filter(
            course_section=section,
            status='ENROLLED'
        ).select_related('student__user').order_by('student__student_number')
        
        # Créer ou récupérer les grades
        for enrollment in enrollments:
            Grade.objects.get_or_create(
                enrollment=enrollment,
                defaults={'graded_by': request.user.professor_profile}
            )
    
    if request.method == 'POST':
        # Traiter les notes en masse
        updated_count = 0
        for key, value in request.POST.items():
            if key.startswith('grade_'):
                grade_id = key.split('_')[1]
                component = key.split('_')[2]
                
                try:
                    grade = Grade.objects.get(id=grade_id)
                    if value:
                        setattr(grade, component, float(value))
                        grade.graded_by = request.user.professor_profile
                        grade.save()
                        updated_count += 1
                except (Grade.DoesNotExist, ValueError):
                    pass
        
        messages.success(request, f'{updated_count} note(s) mise(s) à jour')
        return redirect('grades:admin_grade_bulk_entry') + f'?section_id={section_id}'
    
    # Récupérer les grades existants
    if section:
        grades = Grade.objects.filter(
            enrollment__course_section=section
        ).select_related('enrollment__student__user')
        
        # Créer un dictionnaire enrollment_id -> grade
        grades_dict = {g.enrollment_id: g for g in grades}
    else:
        grades_dict = {}
    for enrollment in enrollments:
        enrollment.grade = grades_dict.get(enrollment.id)
    context = {
        'section': section,
        'enrollments': enrollments,
        'grades_dict': grades_dict,
    }
    
    return render(request, 'grades/grade_bulk_entry.html', context)


@login_required
@user_passes_test(is_admin)
def grade_recalculate(request):
    """Recalculer toutes les notes"""
    
    if request.method == 'POST':
        grades = Grade.objects.all()
        count = 0
        
        for grade in grades:
            grade.save()  # Le signal recalcule automatiquement
            count += 1
        
        messages.success(request, f'{count} note(s) recalculée(s)')
        return redirect('grades:admin_grade_dashboard')
    
    total_grades = Grade.objects.count()
    context = {'total_grades': total_grades}
    return render(request, 'grades/grade_recalculate.html', context)


@login_required
@user_passes_test(is_admin)
def grade_export(request):
    """Exporter les notes en CSV"""
    
    # Récupérer les filtres de la session
    grades = Grade.objects.select_related(
        'enrollment__student__user',
        'enrollment__course_section__course',
        'graded_by__user'
    ).order_by(
        'enrollment__student__student_number',
        'enrollment__course_section__course__code'
    )
    
    # Appliquer les mêmes filtres que la liste
    student_number = request.GET.get('student_number')
    course_code = request.GET.get('course_code')
    
    if student_number:
        grades = grades.filter(
            enrollment__student__student_number__icontains=student_number
        )
    if course_code:
        grades = grades.filter(
            enrollment__course_section__course__code__icontains=course_code
        )
    
    # Créer le CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="notes_export.csv"'
    response.write('\ufeff')  # BOM pour Excel
    
    writer = csv.writer(response)
    writer.writerow([
        'Matricule',
        'Nom complet',
        'Code cours',
        'Section',
        'Mi-parcours',
        'Examen final',
        'Travaux',
        'Participation',
        'Projet',
        'Note finale',
        'Mention',
        'Professeur',
        'Date modification'
    ])
    
    for grade in grades:
        writer.writerow([
            grade.enrollment.student.student_number,
            grade.enrollment.student.user.get_full_name(),
            grade.enrollment.course_section.course.code,
            grade.enrollment.course_section.section_number,
            grade.midterm_exam or '',
            grade.final_exam or '',
            grade.assignments or '',
            grade.participation or '',
            grade.project or '',
            grade.final_grade or '',
            grade.letter_grade or '',
            grade.graded_by.user.get_full_name() if grade.graded_by else '',
            grade.updated_at.strftime('%d/%m/%Y %H:%M')
        ])
    
    return response


@login_required
@user_passes_test(is_admin)
def grade_statistics(request):
    """Statistiques détaillées des notes"""
    
    from django.db.models import Count, Avg, Max, Min
    
    # Stats globales
    stats = Grade.objects.aggregate(
        total=Count('id'),
        average=Avg('final_grade'),
        highest=Max('final_grade'),
        lowest=Min('final_grade')
    )
    
    # Distribution par mention
    distribution = {
        'A': Grade.objects.filter(letter_grade='A').count(),
        'B': Grade.objects.filter(letter_grade='B').count(),
        'C': Grade.objects.filter(letter_grade='C').count(),
        'D': Grade.objects.filter(letter_grade='D').count(),
        'F': Grade.objects.filter(letter_grade='F').count(),
    }
    
    # Stats par département
    from departments.models import Department
    dept_stats = []
    for dept in Department.objects.all():
        dept_grades = Grade.objects.filter(
            enrollment__course_section__course__department=dept
        ).aggregate(
            count=Count('id'),
            avg=Avg('final_grade')
        )
        if dept_grades['count']:
            dept_stats.append({
                'name': dept.name,
                'count': dept_grades['count'],
                'average': dept_grades['avg']
            })
    
    # Top 10 meilleurs étudiants
    from accounts.models import Student
    top_students = []
    for student in Student.objects.all()[:10]:
        avg = Grade.objects.filter(
            enrollment__student=student
        ).aggregate(Avg('final_grade'))['final_grade__avg']
        
        if avg:
            top_students.append({
                'student': student,
                'average': avg
            })
    
    top_students.sort(key=lambda x: x['average'], reverse=True)
    top_students = top_students[:10]
    # Pourcentage de chaque mention
    percentages = {}
    total = stats['total'] or 0
    if total > 0:
        for grade, count in distribution.items():
            percentages[grade] = (count / total) * 100
    else:
        for grade in distribution.keys():
            percentages[grade] = 0

    
    context = {
        'stats': stats,
        'distribution': distribution,
        'dept_stats': dept_stats,
        'top_students': top_students,
        'percentages': percentages,

    }
    
    return render(request, 'grades/statistics.html', context)


# ========== API AJAX pour recherche rapide ==========

@login_required
@user_passes_test(is_admin)
def grade_search_ajax(request):
    """Recherche AJAX d'étudiants pour l'auto-complétion"""
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    from accounts.models import Student
    students = Student.objects.filter(
        Q(student_number__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query)
    ).select_related('user')[:10]
    
    results = [{
        'id': s.id,
        'text': f"{s.student_number} - {s.user.get_full_name()}"
    } for s in students]
    
    return JsonResponse({'results': results})