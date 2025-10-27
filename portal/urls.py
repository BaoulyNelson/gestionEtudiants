# apps/portal/urls.py
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('student', views.student_portal_dashboard, name='student_portal_dashboard'),
    path('home_page/', views.home_page_academic, name='home_page_academic'),
    path('faculty/', views.faculty_workspace, name='faculty_workspace'),
    path('departments/', views.department_programs, name='department_programs'),
    path('research/', views.research_publications_hub, name='research_publications_hub'),
    path('recherche/', views.recherche_globale, name='recherche_globale'),


]
