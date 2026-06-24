from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    # Professeurs
    path('sections/',                             views.vue_sections_professeur,    name='sections_professeur'),
    path('section/<int:id_section>/recap/',       views.vue_recap_notes,            name='recap_notes'),
    path('section/<int:id_section>/saisie/',      views.vue_saisie_notes,           name='saisie_notes_professeur'),
    path('note/<int:id_note>/modifier-prof/',     views.modifier_note_professeur,   name='modifier_note_professeur'),
    path('inscription/<int:id_inscription>/note/', views.saisie_modifier_note_professeur, name='saisie_modifier_note_professeur'),
    path('mes-etudiants/',                        views.vue_mes_etudiants,          name='mes_etudiants'),
    path('palmares/',                             views.vue_palmares,               name='palmares'),
    path("palmares/pdf/", views.vue_palmares_pdf, name="palmares_pdf"),  # ← AJOUTER


    # Étudiants
    path('mes-notes/',                            views.vue_mes_notes,              name='mes_notes'),
    path('releve/',                               views.vue_releve_notes,           name='releve_notes'),
    # Dans la section Étudiants, après 'releve/'
    path('releve/telecharger/', views.vue_telecharger_releve, name='telecharger_releve'),
    path('mes-professeurs/',                      views.vue_mes_professeurs,        name='mes_professeurs'),

    # Détails et statistiques
    path('<int:id_note>/',                        views.vue_detail_note,            name='detail_note'),
    path('section/<int:id_section>/statistiques/', views.vue_statistiques_cours,    name='statistiques_cours'),

    # Admin
    path('',                                      views.vue_liste_notes,            name='liste_notes_admin'),
    path('<int:id_note>/modifier/',               views.modifier_note,              name='modifier_note_admin'),
    path('<int:id_note>/supprimer/',              views.supprimer_note,             name='supprimer_note_admin'),
    path('saisie-groupee/',                       views.saisie_notes_groupee,       name='saisie_notes_groupee'),
    path('recalculer/',                           views.recalculer_notes,           name='recalculer_notes'),
    path('exporter/',                             views.exporter_notes,             name='exporter_notes'),
    path('statistiques/',                         views.vue_statistiques_notes,     name='statistiques_notes'),
    path('generer-releve/<int:id_etudiant>/',     views.vue_generer_releve,         name='generer_releve'),
    path('gpa-etudiants/',                        views.vue_gpa_etudiants,          name='gpa_etudiants'),
    path('gpa-etudiants/pdf/',  views.vue_gpa_pdf,        name='gpa_pdf'),        # ← AJOUTER
    # API AJAX
    path('recherche-ajax/',                       views.recherche_note_ajax,        name='recherche_note_ajax'),
    
    path('declaration/',          views.vue_declaration_notes,      name='declaration_notes'),
    path('valider-declarations/', views.vue_valider_notes_declarees, name='valider_notes_declarees'),
]