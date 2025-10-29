# apps/portal/views.py
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect,get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.shortcuts import render
from django.db.models import Q
from accounts.models import User, Student, Professor

from portal.models import Article, Evenement, Annonce, Livre, Personnel, Examen
from admissions.models import Candidature, FAQ
from faculty.models import ProjetRecherche
from courses.models import Course
from departments.models import Department



def faculty_workspace(request):
    return render(request, 'portal/faculty_workspace.html')

def department_programs(request):
    return render(request, 'portal/department_programs.html')

def research_publications_hub(request):
    return render(request, 'portal/research_publications_hub.html')

def student_portal_dashboard(request):
    return render(request, 'portal/student_portal_dashboard.html')

def home_page_academic(request):
    return render(request, 'portal/home_page_academic_institution.html')




def recherche_globale(request):
    query = request.GET.get('q', '').strip()
    resultats = {}
    total_resultats = 0
    
    if query and len(query) >= 2:  # Minimum 2 caractères
        
        # 1. RECHERCHE DANS LES UTILISATEURS
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) 
        )[:10]
        if users:
            resultats['utilisateurs'] = {
                'titre': 'Utilisateurs',
                'items': users,
                'count': users.count(),
                'icon': 'user'
            }
            total_resultats += users.count()
        
        # 2. RECHERCHE DANS LES ÉTUDIANTS
        students = Student.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(student_number__icontains=query) 
        ).select_related('user')[:10]
        if students:
            resultats['etudiants'] = {
                'titre': 'Étudiants',
                'items': students,
                'count': students.count(),
                'icon': 'users'
            }
            total_resultats += students.count()
        
        # 3. RECHERCHE DANS LES PROFESSEURS
        professors = Professor.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query)|
            Q(professor_id__icontains=query)
            
        ).select_related('user', 'department')[:10]
        if professors:
            resultats['professeurs'] = {
                'titre': 'Professeurs',
                'items': professors,
                'count': professors.count(),
                'icon': 'briefcase'
            }
            total_resultats += professors.count()
        
        # 4. RECHERCHE DANS LES DÉPARTEMENTS
        departments = Department.objects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )[:10]
        if departments:
            resultats['departements'] = {
                'titre': 'Départements',
                'items': departments,
                'count': departments.count(),
                'icon': 'building'
            }
            total_resultats += departments.count()
        
        # 5. RECHERCHE DANS LES COURS
        courses = Course.objects.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).select_related('department')[:10]
        if courses:
            resultats['cours'] = {
                'titre': 'Cours',
                'items': courses,
                'count': courses.count(),
                'icon': 'book-open'
            }
            total_resultats += courses.count()
        
        # 6. RECHERCHE DANS LES ARTICLES
        articles = Article.objects.filter(
            Q(titre__icontains=query) |
            Q(contenu__icontains=query) |
            Q(auteur__icontains=query)
        )[:10]
        if articles:
            resultats['articles'] = {
                'titre': 'Articles',
                'items': articles,
                'count': articles.count(),
                'icon': 'newspaper'
            }
            total_resultats += articles.count()
        
        # 7. RECHERCHE DANS LES ÉVÉNEMENTS
        evenements = Evenement.objects.filter(
            Q(titre__icontains=query) |
            Q(description__icontains=query) |
            Q(lieu__icontains=query)
        )[:10]
        if evenements:
            resultats['evenements'] = {
                'titre': 'Événements',
                'items': evenements,
                'count': evenements.count(),
                'icon': 'calendar'
            }
            total_resultats += evenements.count()
        
        # 8. RECHERCHE DANS LES LIVRES
        livres = Livre.objects.filter(
            Q(titre__icontains=query) |
            Q(auteur__icontains=query) 
          
        )[:10]
        if livres:
            resultats['livres'] = {
                'titre': 'Bibliothèque',
                'items': livres,
                'count': livres.count(),
                'icon': 'book'
            }
            total_resultats += livres.count()
        
        # 9. RECHERCHE DANS LES CANDIDATURES
        candidatures = Candidature.objects.filter(
            Q(prenom__icontains=query) |
            Q(nom__icontains=query) |
            Q(email__icontains=query) |
            Q(programme__code__icontains=query)
        )[:10]
        if candidatures:
            resultats['candidatures'] = {
                'titre': 'Candidatures',
                'items': candidatures,
                'count': candidatures.count(),
                'icon': 'clipboard-check'
            }
            total_resultats += candidatures.count()
        
        # 10. RECHERCHE DANS LES PROJETS DE RECHERCHE
        projets = ProjetRecherche.objects.filter(
            Q(titre__icontains=query) |
            Q(description__icontains=query)
        ).select_related('responsable')[:10]
        if projets:
            resultats['projets_recherche'] = {
                'titre': 'Projets de Recherche',
                'items': projets,
                'count': projets.count(),
                'icon': 'flask'
            }
            total_resultats += projets.count()
        
        # 11. RECHERCHE DANS LES ANNONCES
        annonces = Annonce.objects.filter(
            Q(titre__icontains=query) |
            Q(contenu__icontains=query)
        )[:10]
        if annonces:
            resultats['annonces'] = {
                'titre': 'Annonces',
                'items': annonces,
                'count': annonces.count(),
                'icon': 'megaphone'
            }
            total_resultats += annonces.count()
        
        # 12. RECHERCHE DANS LE PERSONNEL
        personnel = Personnel.objects.filter(
            Q(nom__icontains=query) |
            Q(poste=query) |
            Q(nom=query)
        )[:10]
        if personnel:
            resultats['personnel'] = {
                'titre': 'Personnel',
                'items': personnel,
                'count': personnel.count(),
                'icon': 'id-card'
            }
            total_resultats += personnel.count()
        
        # 13. RECHERCHE DANS LES FAQ
        faqs = FAQ.objects.filter(
            Q(question__icontains=query) |
            Q(reponse__icontains=query)
        )[:10]
        if faqs:
            resultats['faqs'] = {
                'titre': 'Questions Fréquentes',
                'items': faqs,
                'count': faqs.count(),
                'icon': 'question-circle'
            }
            total_resultats += faqs.count()
    
    context = {
        'query': query,
        'resultats': resultats,
        'total_resultats': total_resultats,
    }
    
    return render(request, 'portal/recherche_globale.html', context)




