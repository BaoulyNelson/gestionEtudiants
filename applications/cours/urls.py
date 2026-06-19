from django.urls import path
from . import views

app_name = 'cours'

urlpatterns = [
    # ── Cours ────────────────────────────────────────────────────────────────
    path('',                        views.liste_cours,    name='liste_cours'),
    path('<int:id_cours>/',        views.detail_cours,   name='detail_cours'),
    path('creer/',                  views.creer_cours,    name='creer_cours'),
    path('<int:id_cours>/modifier/',   views.modifier_cours,   name='modifier_cours'),
    path('<int:id_cours>/desactiver/', views.desactiver_cours,  name='desactiver_cours'),

    # ── Sections ─────────────────────────────────────────────────────────────
    path('sections/',                                   views.liste_sections,           name='liste_sections'),
    path('sections/<int:id_section>/',                  views.detail_section,           name='detail_section'),
    path('sections/creer/',                             views.creer_section,            name='creer_section'),
    path('sections/creer/<int:id_cours>/',             views.creer_section,            name='creer_section_pour_cours'),
    path('sections/<int:id_section>/modifier/',         views.modifier_section,         name='modifier_section'),
    path('sections/<int:id_section>/supprimer/',                views.supprimer_section,        name='supprimer_section'),
    path('sections/<int:id_section>/basculer/',         views.basculer_ouverture_section, name='basculer_section'),

    # ── Mes cours ────────────────────────────────────────────────────────────
    path('mes-cours/', views.mes_cours, name='mes_cours'),
]