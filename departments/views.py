from django.shortcuts import render
from departments.models import Department
from django.shortcuts import render, get_object_or_404
from departments.models import Department
from django.contrib.auth.decorators import login_required
from courses.models import Course


def department_list(request):
    departments = Department.objects.all()  # récupère tous les départements
    return render(request, 'departments/list.html', {'departments': departments})


@login_required
def courses_by_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    courses = Course.objects.filter(department=department)
    return render(request, 'courses/list_by_department.html', {
        'department': department,
        'courses': courses
    })
