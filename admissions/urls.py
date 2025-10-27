from django.urls import path
from . import views


app_name = 'admissions'

urlpatterns = [
    # Avec fonction
    path('admission/', views.soumettre_candidature, name='admission_home'),
    path('condition/', views.conditions_admission, name='conditions_admission'),
    path('politique_confidentialite/', views.politique_confidentialite, name='politique_confidentialite'),
    path('', views.admission_center, name='admision_center'),
    
    path('confirmation/<int:pk>/', views.candidature_confirmation, name='candidature_confirmation'),
    

]

