from django.urls import path
from . import views
from django.contrib.auth import views as vues_auth
from django.urls import reverse_lazy
from applications.portail.models import SiteSettings

app_name = 'comptes'

urlpatterns = [
    # Authentification
    path('connexion/', views.vue_connexion, name='connexion'),
    path('deconnexion/', views.vue_deconnexion, name='deconnexion'),
    path('changer-mot-de-passe/', views.vue_changer_mot_de_passe, name='changer_mot_de_passe'),
    path('tableau-de-bord/', views.tableau_bord, name='tableau_bord'),

    # Profil
    path('profil/', views.vue_profil, name='profil'),
    path('profil/badge/pdf/', views.badge_pdf, name='badge_pdf'),
    path('profil/badge/png/', views.badge_png, name='badge_png'),

    # Gestion utilisateurs (admin)
    path('utilisateurs/', views.vue_liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/creer/', views.vue_creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/<int:utilisateur_id>/modifier/', views.vue_modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/<int:utilisateur_id>/basculer/', views.vue_basculer_actif, name='basculer_actif'),
    path('utilisateurs/<int:utilisateur_id>/reinitialiser-mdp/', views.vue_reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),
    path('professeurs/', views.vue_liste_professeurs, name='liste_professeurs'),
    path('professeur/<int:pk>/', views.vue_detail_professeur, name='detail_professeur'),
    path('etudiants/', views.vue_liste_etudiants, name='liste_etudiants'),
    path('etudiant/<int:pk>/', views.vue_detail_etudiant, name='detail_etudiant'),

    # Réinitialisation mot de passe


    path('reinitialisation/', vues_auth.PasswordResetView.as_view(
        template_name='comptes/reinitialisation_mdp_formulaire.html',
        email_template_name='comptes/reinitialisation_mdp_email.txt',
        html_email_template_name='comptes/reinitialisation_mdp_email.html',  # ← ajout
        success_url=reverse_lazy('comptes:reinitialisation_done'),
        extra_email_context={'site': SiteSettings.get()},
    ), name='reinitialisation'),
    
    path('reinitialisation/envoye/', vues_auth.PasswordResetDoneView.as_view(
        template_name='comptes/reinitialisation_mdp_envoye.html',
    ), name='reinitialisation_done'),

    path('reinitialisation/<uidb64>/<token>/', vues_auth.PasswordResetConfirmView.as_view(
        template_name='comptes/reinitialisation_mdp_confirmation.html',
        success_url=reverse_lazy('comptes:reinitialisation_complete'),
    ), name='password_reset_confirm'),  # ← nom Django attendu, ne pas changer

    path('reinitialisation/complete/', vues_auth.PasswordResetCompleteView.as_view(
        template_name='comptes/reinitialisation_mdp_complete.html',
    ), name='reinitialisation_complete'),
]