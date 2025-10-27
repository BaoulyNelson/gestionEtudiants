from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    # Inscriptions étudiants
    path('available/', views.available_sections_view, name='available_sections'),
    path('enroll/<int:section_id>/', views.enroll_view, name='enroll'),
    path('drop/<int:enrollment_id>/', views.drop_enrollment_view, name='drop_enrollment'),
    path('my-enrollments/', views.my_enrollments_view, name='my_enrollments'),
    
    # Gestion des inscriptions (admin)
    path('', views.enrollment_list_view, name='enrollment_list'),
    path('<int:enrollment_id>/update-status/', views.enrollment_update_status_view, name='update_status'),
    path('<int:enrollment_id>/history/', views.enrollment_history_view, name='enrollment_history'),
]