from django.urls import path
from . import views

app_name = 'faculty'

urlpatterns = [
    # Espace de travail principal
    path('', views.faculty_workspace, name='workspace'),
    
    # Gestion des cours
    path('courses/', views.faculty_courses, name='faculty_courses'),
    # path('courses/create/', views.create_course, name='create_course'),
    # path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    # path('courses/<int:pk>/edit/', views.edit_course, name='edit_course'),
    # path('courses/<int:pk>/delete/', views.delete_course, name='delete_course'),
    
    # Gestion des évaluations
    path('evaluations/', views.faculty_evaluations, name='faculty_evaluations'),
    # path('evaluations/<int:pk>/', views.evaluate_submission, name='evaluate_submission'),
    # path('evaluations/<int:pk>/download/', views.download_submission, name='download_submission'),
    
    # Calendrier et événements
    # path('calendar/', views.faculty_calendar, name='faculty_calendar'),
    # path('events/create/', views.create_event, name='create_event'),
    # path('events/<int:pk>/edit/', views.edit_event, name='edit_event'),
    # path('events/<int:pk>/delete/', views.delete_event, name='delete_event'),
    
    # Messages
    path('messages/', views.faculty_messages, name='faculty_messages'),
    # path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    # path('messages/compose/', views.compose_message, name='compose_message'),
    # path('messages/<int:pk>/delete/', views.delete_message, name='delete_message'),
    
    # Projets de recherche
    path('research/', views.faculty_research, name='faculty_research'),
    # path('research/create/', views.create_project, name='create_project'),
    # path('research/<int:pk>/', views.project_detail, name='project_detail'),
    # path('research/<int:pk>/edit/', views.edit_project, name='edit_project'),
    # path('research/<int:pk>/delete/', views.delete_project, name='delete_project'),
    
    # Profil
    path('profile/', views.faculty_profile, name='faculty_profile'),
    # path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # # Paramètres
    # path('settings/', views.faculty_settings, name='faculty_settings'),
    
    # # Statistiques et rapports
    # path('statistics/', views.faculty_statistics, name='faculty_statistics'),
    # path('reports/', views.faculty_reports, name='faculty_reports'),
]