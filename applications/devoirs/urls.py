from django.urls import path
from . import views

app_name = 'devoirs'

urlpatterns = [
    # ── Professeur ──────────────────────────────────────────────────────────
    path('',
         views.liste_devoirs_prof,    name='liste_devoirs'),

    path('creer/<int:section_id>/',
         views.creer_devoir,          name='creer_devoir'),

    path('<int:devoir_id>/',
         views.detail_devoir,         name='detail_devoir'),

    path('<int:devoir_id>/modifier/',
         views.modifier_devoir,       name='modifier_devoir'),

    path('<int:devoir_id>/supprimer/',
         views.supprimer_devoir,      name='supprimer_devoir'),

    path('<int:devoir_id>/publier/',
         views.basculer_publication,  name='basculer_publication'),

    path('<int:devoir_id>/remises/',
         views.liste_remises,         name='liste_remises'),

    path('<int:devoir_id>/remises/telecharger/',
         views.telecharger_remises,   name='telecharger_remises'),

    path('remise/<int:remise_id>/noter/',
         views.noter_remise,          name='noter_remise'),

    path('fichier-devoir/<int:fichier_id>/supprimer/',
         views.supprimer_fichier_devoir, name='supprimer_fichier_devoir'),

    # ── Étudiant ────────────────────────────────────────────────────────────
    path('mes-devoirs/',
         views.mes_devoirs,                name='mes_devoirs'),

    path('<int:devoir_id>/voir/',
         views.detail_devoir_etudiant,     name='detail_devoir_etudiant'),

    path('<int:devoir_id>/remettre/',
         views.remettre_devoir,            name='remettre_devoir'),
]
