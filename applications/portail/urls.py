from django.urls import path
from . import views

app_name = 'portail'


urlpatterns = [
    path('', views.vue_accueil, name='accueil'),
    path('parametres/', views.vue_parametres_site, name='parametres_site'),
    path('recherche/', views.recherche_globale, name='recherche_globale'),
]