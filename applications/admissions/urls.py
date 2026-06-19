from django.urls import path
from . import views


app_name = 'admissions'

urlpatterns = [
    # Avec fonction
    path('admission/', views.soumettre_candidature, name='liste_admissions'),
    path('condition/', views.conditions_admission, name='conditions_admission'),
    path('politique_confidentialite/', views.politique_confidentialite, name='politique_confidentialite'),
    path('', views.centre_admissions, name='centre_admissions'),
    
    path('confirmation/<int:pk>/', views.candidature_confirmation, name='candidature_confirmation'),
    

]

