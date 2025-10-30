

# ========== enrollments/urls.py ==========

from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    # ===== Vues Étudiant =====
    path('available/', views.available_sections_view, name='available_sections'),
    path('my-enrollments/', views.my_enrollments_view, name='my_enrollments'),
    path('enroll/<int:section_id>/', views.enroll_view, name='enroll'),
    path('drop/<int:enrollment_id>/', views.drop_enrollment_view, name='drop_enrollment'),
    
    # ===== Vues Admin =====
    path('list/', views.enrollment_list_view, name='enrollment_list'),
    path('create/', views.enrollment_create_view, name='enrollment_create'),
    path('<int:enrollment_id>/update/', views.enrollment_update_view, name='enrollment_update'),
    path('<int:enrollment_id>/delete/', views.enrollment_delete_view, name='enrollment_delete'),
    path('<int:enrollment_id>/update-status/', views.enrollment_update_status_view, name='enrollment_update_status'),
    
    # ===== Historique =====
    path('<int:enrollment_id>/history/', views.enrollment_history_view, name='enrollment_history'),
]
