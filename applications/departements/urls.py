from django.urls import path
from . import views

app_name = 'departements'

urlpatterns = [
    path('', views.liste_departements, name='liste_departements'),
    path('<int:id_departement>/cours/', views.cours_par_departement, name='liste_par_departement'),
]