from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.department_list, name='list'),
    path('department/<int:department_id>/courses/', views.courses_by_department, name='list_by_department'),
    


]
