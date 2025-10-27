from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Cours, Soumission, EvenementCalendrier,
    Message, ProjetRecherche
)
from accounts.models import User, Professor


@login_required
def faculty_workspace(request):
    """
    Vue principale de l'espace de travail des professeurs
    """
    # Vérifier que l'utilisateur est bien un professeur
    if not request.user.is_professor():
        messages.error(request, "Accès refusé. Cette section est réservée aux professeurs.")
        return redirect('home')
    
    # Récupérer le profil professeur
    try:
        professeur = request.user.professor_profile
    except Professor.DoesNotExist:
        messages.error(
            request, 
            "Votre profil professeur n'existe pas. Veuillez contacter l'administration."
        )
        return redirect('home')
    
    # Statistiques du dashboard
    cours_actifs = Cours.objects.filter(
        professeur=professeur, 
        statut='actif'
    )
    nombre_cours_actifs = cours_actifs.count()
    
    # Total d'étudiants (ajustez selon votre logique)
    total_etudiants = cours_actifs.aggregate(
        total=Count('etudiants', distinct=True)  # Si relation ManyToMany
    )['total'] or 0
    
    # Évaluations en attente
    evaluations_en_attente = Soumission.objects.filter(
        cours__professeur=professeur,
        statut='en_attente'
    ).count()
    
    # Projets de recherche
    projets_recherche = ProjetRecherche.objects.filter(
        responsable=professeur
    )
    
    # Messages non lus
    messages_non_lus = Message.objects.filter(
        destinataire=professeur,
        lu=False
    ).count()
    
    # Cours avec statistiques détaillées
    cours_avec_stats = cours_actifs.annotate(
        soumissions_attente=Count(
            'soumissions',
            filter=Q(soumissions__statut='en_attente')
        ),
        total_soumissions=Count('soumissions')
    )
    
    # Soumissions récentes à évaluer
    soumissions_recentes = Soumission.objects.filter(
        cours__professeur=professeur,
        statut='en_attente'
    ).select_related(
        'cours', 
        'etudiant__user'
    ).order_by('-date_soumission')[:5]
    
    # Événements du calendrier (prochains 7 jours)
    date_debut = timezone.now()
    date_fin = date_debut + timedelta(days=7)
    evenements_prochains = EvenementCalendrier.objects.filter(
        cours__professeur=professeur,
        date_debut__gte=date_debut,
        date_debut__lte=date_fin
    ).select_related('cours').order_by('date_debut')[:5]
    
    # Messages récents
    messages_recents = Message.objects.filter(
        destinataire=professeur
    ).select_related('expediteur__user').order_by('-date_envoi')[:5]
    
    # Projets de recherche actifs
    projets_actifs = projets_recherche.filter(
        statut__in=['en_cours', 'revision']
    ).order_by('-date_debut')[:3]
    
    # Activité récente (optionnel)
    activites_recentes = []
    
    # Ajouter les dernières soumissions
    for soumission in soumissions_recentes[:3]:
        activites_recentes.append({
            'type': 'soumission',
            'titre': f"Nouvelle soumission pour {soumission.cours.nom}",
            'description': f"{soumission.etudiant.user.get_full_name()}",
            'date': soumission.date_soumission,
            'icon': 'file-earmark-text'
        })
    
    # Ajouter les prochains événements
    for evenement in evenements_prochains[:2]:
        activites_recentes.append({
            'type': 'evenement',
            'titre': evenement.titre,
            'description': f"{evenement.cours.nom}",
            'date': evenement.date_debut,
            'icon': 'calendar-event'
        })
    
    # Trier par date
    activites_recentes.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'professeur': professeur,
        'user': request.user,  # Pour accéder aux infos du User
        
        # Statistiques principales
        'nombre_cours_actifs': nombre_cours_actifs,
        'total_etudiants': total_etudiants,
        'evaluations_en_attente': evaluations_en_attente,
        'nombre_projets_recherche': projets_recherche.count(),
        'messages_non_lus': messages_non_lus,
        
        # Données détaillées
        'cours_actifs': cours_avec_stats,
        'soumissions_recentes': soumissions_recentes,
        'evenements_prochains': evenements_prochains,
        'messages_recents': messages_recents,
        'projets_actifs': projets_actifs,
        'activites_recentes': activites_recentes[:5],
    }
    
    return render(request, 'faculty/workspace.html', context)


@login_required
def faculty_courses(request):
    """
    Vue pour lister tous les cours du professeur
    """
    if not request.user.is_professor():
        messages.error(request, "Accès refusé.")
        return redirect('home')
    
    professeur = request.user.professor_profile
    
    # Filtrer les cours selon le statut
    statut_filtre = request.GET.get('statut', 'all')
    
    cours = Cours.objects.filter(professeur=professeur)
    
    if statut_filtre != 'all':
        cours = cours.filter(statut=statut_filtre)
    
    # Ajouter des statistiques
    cours = cours.annotate(
        total_etudiants=Count('etudiants'),
        soumissions_attente=Count(
            'soumissions',
            filter=Q(soumissions__statut='en_attente')
        )
    ).order_by('-date_creation')
    
    context = {
        'professeur': professeur,
        'cours': cours,
        'statut_filtre': statut_filtre,
    }
    
    return render(request, 'faculty/courses.html', context)


@login_required
def faculty_evaluations(request):
    """
    Vue pour gérer les évaluations
    """
    if not request.user.is_professor():
        messages.error(request, "Accès refusé.")
        return redirect('home')
    
    professeur = request.user.professor_profile
    
    # Filtrer les soumissions
    statut_filtre = request.GET.get('statut', 'en_attente')
    cours_filtre = request.GET.get('cours', 'all')
    
    soumissions = Soumission.objects.filter(
        cours__professeur=professeur
    ).select_related('cours', 'etudiant__user')
    
    if statut_filtre != 'all':
        soumissions = soumissions.filter(statut=statut_filtre)
    
    if cours_filtre != 'all':
        soumissions = soumissions.filter(cours_id=cours_filtre)
    
    soumissions = soumissions.order_by('-date_soumission')
    
    # Liste des cours pour le filtre
    cours_list = Cours.objects.filter(
        professeur=professeur,
        statut='actif'
    ).order_by('nom')
    
    context = {
        'professeur': professeur,
        'soumissions': soumissions,
        'cours_list': cours_list,
        'statut_filtre': statut_filtre,
        'cours_filtre': cours_filtre,
    }
    
    return render(request, 'faculty/evaluations.html', context)


@login_required
def faculty_research(request):
    """
    Vue pour gérer les projets de recherche
    """
    if not request.user.is_professor():
        messages.error(request, "Accès refusé.")
        return redirect('home')
    
    professeur = request.user.professor_profile
    
    # Projets du professeur
    projets = ProjetRecherche.objects.filter(
        responsable=professeur
    ).order_by('-date_debut')
    
    # Statistiques
    projets_stats = {
        'total': projets.count(),
        'en_cours': projets.filter(statut='en_cours').count(),
        'termines': projets.filter(statut='termine').count(),
        'en_revision': projets.filter(statut='revision').count(),
    }
    
    context = {
        'professeur': professeur,
        'projets': projets,
        'projets_stats': projets_stats,
    }
    
    return render(request, 'faculty/research.html', context)


@login_required
def faculty_messages(request):
    """
    Vue pour gérer les messages
    """
    if not request.user.is_professor():
        messages.error(request, "Accès refusé.")
        return redirect('home')
    
    professeur = request.user.professor_profile
    
    # Messages reçus
    messages_recus = Message.objects.filter(
        destinataire=professeur
    ).select_related('expediteur__user').order_by('-date_envoi')
    
    # Marquer comme lus (optionnel)
    if request.GET.get('mark_read'):
        messages_recus.filter(lu=False).update(lu=True)
    
    context = {
        'professeur': professeur,
        'messages': messages_recus,
    }
    
    return render(request, 'faculty/messages.html', context)


@login_required
def faculty_profile(request):
    """
    Vue pour gérer le profil du professeur
    """
    if not request.user.is_professor():
        messages.error(request, "Accès refusé.")
        return redirect('home')
    
    professeur = request.user.professor_profile
    user = request.user
    
    if request.method == 'POST':
        # Mettre à jour les informations
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.address = request.POST.get('address', user.address)
        
        # Photo de profil
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Mettre à jour les champs du professeur
        professeur.specialization = request.POST.get('specialization', professeur.specialization)
        professeur.save()
        
        messages.success(request, "Profil mis à jour avec succès!")
        return redirect('faculty_profile')
    
    context = {
        'professeur': professeur,
        'user': user,
    }
    
    return render(request, 'faculty/profile.html', context)












