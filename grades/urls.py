from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # Professeurs
    path('professor/sections/', views.professor_sections_view, name='professor_sections'),
    path('professor/section/<int:section_id>/grade-entry/', views.grade_entry_view, name='grade_entry'),
    path('my_students/', views.my_students_view, name='my_students'),
    path('professor/palmares/', views.palmares_view, name='palmares'),
    path('professor/section/<int:section_id>/summary/', views.grades_summary_view, name='grades_summary'),

    
    
    # Étudiants
    path('my-grades/', views.my_grades_view, name='my_grades'),
    path('transcript/', views.transcript_view, name='transcript'),
    path('my_professors/', views.my_professors_view, name='my_professors'),
    
    # Détails et statistiques
    path('<int:grade_id>/', views.grade_detail_view, name='grade_detail'),
    path('section/<int:section_id>/statistics/', views.course_statistics_view, name='course_statistics'),
    
    # Admin
    path('', views.grade_list_view, name='grade_list'),
    path('generate-transcript/<int:student_id>/', views.generate_transcript_view, name='generate_transcript'),
    path('students-gpa/', views.students_gpa_view, name='students_gpa'),

]