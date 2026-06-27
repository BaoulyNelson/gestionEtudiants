from django.urls import path
from . import views

app_name = 'portail'

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

    # Personnel
    path('personnel/',                              views.vue_liste_personnel,    name='liste_personnel'),
    path('personnel/creer/',                        views.vue_creer_personnel,    name='creer_personnel'),
    path('personnel/<int:personnel_id>/modifier/',  views.vue_modifier_personnel, name='modifier_personnel'),
    path('personnel/<int:personnel_id>/supprimer/', views.vue_supprimer_personnel,name='supprimer_personnel'),

    # ── Livres : catalogue ────────────────────────────────────────────────────
    path('livres/',                          views.vue_liste_livres,    name='liste_livres'),
    path('livres/<int:livre_id>/',           views.vue_detail_livre,    name='detail_livre'),       # ← nouveau

    # ── Livres : CRUD admin ───────────────────────────────────────────────────
    path('livres/creer/',                    views.vue_creer_livre,     name='creer_livre'),
    path('livres/<int:livre_id>/modifier/',  views.vue_modifier_livre,  name='modifier_livre'),
    path('livres/<int:livre_id>/supprimer/', views.vue_supprimer_livre, name='supprimer_livre'),

    # ── Livres : emprunts ─────────────────────────────────────────────────────
    path('livres/mes-emprunts/',                              views.vue_mes_emprunts, name='mes_emprunts'),                  # ← nouveau
    path('livres/<int:livre_id>/emprunter/',                  views.vue_emprunter,    name='emprunter'),                     # ← nouveau
    path('livres/emprunts/<int:emprunt_id>/retourner/',       views.vue_retourner,    name='retourner'),                     # ← nouveau

    # ── Livres : réservations ─────────────────────────────────────────────────
    path('livres/<int:livre_id>/reserver/',                          views.vue_reserver,           name='reserver'),           # ← nouveau
    path('livres/reservations/<int:reservation_id>/annuler/',        views.vue_annuler_reservation, name='annuler_reservation'),# ← nouveau

    # ── Livres : administration ───────────────────────────────────────────────
    path('livres/admin/emprunts/',                            views.vue_gestion_emprunts,          name='gestion_emprunts'),          # ← nouveau
    path('livres/admin/emprunts/<int:emprunt_id>/retour/',    views.vue_enregistrer_retour_admin,  name='enregistrer_retour_admin'),   # ← nouveau
]