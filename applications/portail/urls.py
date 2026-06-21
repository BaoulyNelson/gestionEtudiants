from django.urls import path
from . import views

app_name = 'portail'


# portail/urls.py
urlpatterns = [
    path('', views.vue_accueil, name='accueil'),
    path('parametres/', views.vue_parametres_site, name='parametres_site'),
    path('recherche/',  views.recherche_globale,   name='recherche_globale'),
    path('newsletter/', views.vue_newsletter,       name='newsletter'),

    # Examens
    path('examens/',                             views.vue_liste_examens,    name='liste_examens'),
    path('examens/creer/',                       views.vue_creer_examen,     name='creer_examen'),
    path('examens/<int:examen_id>/modifier/',    views.vue_modifier_examen,  name='modifier_examen'),
    path('examens/<int:examen_id>/supprimer/',   views.vue_supprimer_examen, name='supprimer_examen'),
]