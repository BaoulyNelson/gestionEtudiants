from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from applications.comptes.models import Utilisateur, Etudiant, Professeur
from applications.portail.models import Livre, Personnel
from applications.admissions.models import Candidature, FAQ
from applications.cours.models import Cours
from applications.departements.models import Departement
from applications.articles.models import Article, Evenement,Annonce


# ──────────────────────────────────────────────────────────────
# PAGES STATIQUES / PORTAILS
# ──────────────────────────────────────────────────────────────
def vue_accueil(request):
    """Page d'accueil"""
    if request.user.is_authenticated:
        return redirect("comptes:tableau_bord")
    return render(request, "accueil.html")




from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import SiteSettings
from .forms import FormulaireParametresSite
from applications.comptes.views import est_administrateur



@login_required
@user_passes_test(est_administrateur)
def vue_parametres_site(request):
    site = SiteSettings.get()
    form = FormulaireParametresSite(
        request.POST or None,
        request.FILES or None,  # ← indispensable pour les images
        instance=site
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Paramètres mis à jour avec succès.")
        return redirect("portail:parametres_site")
    return render(request, "portail/parametres_site.html", {"form": form, "site": site})
# ──────────────────────────────────────────────────────────────
# RECHERCHE GLOBALE
# ──────────────────────────────────────────────────────────────

def recherche_globale(request):
    """
    Recherche transversale sur l'ensemble des entités du système :
    utilisateurs, étudiants, professeurs, départements, cours,
    articles, événements, livres, candidatures, projets,
    annonces, personnel et FAQ.
    """
    requete          = request.GET.get('q', '').strip()
    resultats        = {}
    total_resultats  = 0

    if len(requete) >= 2:

        # 1. Utilisateurs
        utilisateurs = Utilisateur.objects.filter(
            Q(first_name__icontains=requete)
            | Q(last_name__icontains=requete)
            | Q(email__icontains=requete)
        )[:10]
        if utilisateurs:
            resultats['utilisateurs'] = {
                'titre': 'Utilisateurs',
                'items': utilisateurs,
                'nombre': utilisateurs.count(),
                'icone': 'user',
            }
            total_resultats += utilisateurs.count()

            
            
            
        # 2. Étudiants
        etudiants = Etudiant.objects.filter(
            Q(utilisateur__first_name__icontains=requete)
            | Q(utilisateur__last_name__icontains=requete)
            | Q(utilisateur__email__icontains=requete)
            | Q(numero_etudiant__icontains=requete)        # student_number → numero_etudiant
        ).select_related('utilisateur')[:10]               # user → utilisateur

        # 3. Professeurs
        professeurs = Professeur.objects.filter(
            Q(utilisateur__first_name__icontains=requete)
            | Q(utilisateur__last_name__icontains=requete)
            | Q(specialite__icontains=requete)             # specialization → specialite
            | Q(identifiant_professeur__icontains=requete) # professor_id → identifiant_professeur
        ).select_related('utilisateur', 'departement')[:10] # user/department → utilisateur/departement

        # 4. Départements
        departements = Departement.objects.filter(
            Q(nom__icontains=requete)                      # name → nom
            | Q(code__icontains=requete)
            | Q(description__icontains=requete)
        )[:10]

        # 5. Cours
        cours = Cours.objects.filter(
            Q(code__icontains=requete)
            | Q(nom__icontains=requete)                    # name → nom
            | Q(description__icontains=requete)
        ).select_related('departement')[:10]               # department → departement

        # 6. Articles
        articles = Article.objects.filter(
            Q(titre__icontains=requete)
            | Q(contenu__icontains=requete)
            | Q(auteur__icontains=requete)
        )[:10]
        if articles:
            resultats['articles'] = {
                'titre': 'Articles',
                'items': articles,
                'nombre': articles.count(),
                'icone': 'newspaper',
            }
            total_resultats += articles.count()

        # 7. Événements
        evenements = Evenement.objects.filter(
            Q(titre__icontains=requete)
            | Q(description__icontains=requete)
            | Q(lieu__icontains=requete)
        )[:10]
        if evenements:
            resultats['evenements'] = {
                'titre': 'Événements',
                'items': evenements,
                'nombre': evenements.count(),
                'icone': 'calendar',
            }
            total_resultats += evenements.count()

        # 8. Bibliothèque
        livres = Livre.objects.filter(
            Q(titre__icontains=requete)
            | Q(auteur__icontains=requete)
        )[:10]
        if livres:
            resultats['livres'] = {
                'titre': 'Bibliothèque',
                'items': livres,
                'nombre': livres.count(),
                'icone': 'book',
            }
            total_resultats += livres.count()

        # 9. Candidatures
        candidatures = Candidature.objects.filter(
            Q(prenom__icontains=requete)
            | Q(nom__icontains=requete)
            | Q(email__icontains=requete)
            | Q(programme__code__icontains=requete)
        )[:10]
        if candidatures:
            resultats['candidatures'] = {
                'titre': 'Candidatures',
                'items': candidatures,
                'nombre': candidatures.count(),
                'icone': 'clipboard-check',
            }
            total_resultats += candidatures.count()



        # 11. Annonces
        annonces = Annonce.objects.filter(
            Q(titre__icontains=requete)
            | Q(contenu__icontains=requete)
        )[:10]
        if annonces:
            resultats['annonces'] = {
                'titre': 'Annonces',
                'items': annonces,
                'nombre': annonces.count(),
                'icone': 'megaphone',
            }
            total_resultats += annonces.count()

        # 12. Personnel
        membres_personnel = Personnel.objects.filter(
            Q(nom__icontains=requete)
            | Q(poste__icontains=requete)
        )[:10]
        if membres_personnel:
            resultats['personnel'] = {
                'titre': 'Personnel',
                'items': membres_personnel,
                'nombre': membres_personnel.count(),
                'icone': 'id-card',
            }
            total_resultats += membres_personnel.count()

        # 13. FAQ
        faqs = FAQ.objects.filter(
            Q(question__icontains=requete)
            | Q(reponse__icontains=requete)
        )[:10]
        if faqs:
            resultats['faqs'] = {
                'titre': 'Questions Fréquentes',
                'items': faqs,
                'nombre': faqs.count(),
                'icone': 'question-circle',
            }
            total_resultats += faqs.count()

    contexte = {
        'requete':         requete,
        'resultats':       resultats,
        'total_resultats': total_resultats,
    }
    return render(request, 'portail/recherche_globale.html', contexte)
