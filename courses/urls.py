from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Cours
    path('', views.course_list_view, name='course_list'),
    path('<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('create/', views.course_create_view, name='course_create'),
    path('<int:course_id>/update/', views.course_update_view, name='course_update'),
    path('<int:course_id>/delete/', views.course_delete_view, name='course_delete'),
    
    # Sections
    path('sections/', views.section_list_view, name='section_list'),
    path('sections/<int:section_id>/', views.section_detail_view, name='section_detail'),
    path('sections/create/', views.section_create_view, name='section_create'),
    path('sections/create/<int:course_id>/', views.section_create_view, name='section_create_for_course'),
    path('sections/<int:section_id>/update/', views.section_update_view, name='section_update'),
    path('sections/<int:section_id>/toggle-open/', views.section_toggle_open_view, name='section_toggle_open'),
    
    # Mes cours
    path('my-courses/', views.my_courses_view, name='my_courses'),
]