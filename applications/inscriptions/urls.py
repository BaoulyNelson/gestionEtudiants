from django.urls import path
from . import views

app_name = 'inscriptions'

urlpatterns = [
    # ===== Vues Étudiant =====
    path('disponibles/',                          views.vue_sections_disponibles,   name='sections_disponibles'),
    path('mes-inscriptions/',                     views.vue_mes_inscriptions,        name='mes_inscriptions'),
    path('inscrire/<int:id_section>/',            views.vue_inscrire,                name='inscrire'),
    path('abandonner/<int:id_inscription>/',      views.vue_abandonner,              name='abandonner'),
    path('reprendre/<int:id_inscription>/',       views.vue_reprendre,               name='reprendre'),

    # ===== Vues Admin =====
    path('liste/',                                views.vue_liste_inscriptions,      name='liste_inscriptions'),
    path('creer/',                                views.vue_creer_inscription,       name='creer_inscription'),
    path('<int:id_inscription>/modifier/',        views.vue_modifier_inscription,    name='modifier_inscription'),
    path('<int:id_inscription>/supprimer/',       views.vue_supprimer_inscription,   name='supprimer_inscription'),
    path('<int:id_inscription>/modifier-statut/', views.vue_modifier_statut,         name='modifier_statut'),
    path('ajax/sections/<int:etudiant_id>/',      views.sections_pour_etudiant,      name='ajax_sections_etudiant'),

    # ===== Historique =====
    path('<int:id_inscription>/historique/',      views.vue_historique_inscription,  name='historique_inscription'),
]