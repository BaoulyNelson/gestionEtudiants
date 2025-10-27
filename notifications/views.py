# ========== notifications/views.py (CORRIGÉ) ==========
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification


@login_required
def mes_notifications(request):
    """Affiche toutes les notifications de l'utilisateur"""
    
    # Traiter les actions POST (marquer comme lue)
    if request.method == 'POST':
        action = request.POST.get('action')
        notif_id = request.POST.get('notif_id')
        
        if action == 'marquer_lue' and notif_id:
            notification = get_object_or_404(
                Notification, 
                id=notif_id, 
                utilisateur=request.user
            )
            notification.marquer_comme_lue()
            messages.success(request, "✅ Notification marquée comme lue.")
        
        elif action == 'marquer_toutes_lues':
            # Marquer toutes les notifications comme lues
            count = Notification.objects.filter(
                utilisateur=request.user,
                est_lue=False
            ).update(est_lue=True)
            messages.success(request, f"✅ {count} notification(s) marquée(s) comme lue(s).")
        
        # Rediriger pour rafraîchir la page
        return redirect('notifications:mes_notifications')
    
    # Récupérer les notifications
    notifications = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')
    
    # Compter les notifications non lues
    notifications_non_lues = notifications.filter(est_lue=False)
    
    context = {
        'notifications': notifications,
        'notifications_non_lues': notifications_non_lues,
    }
    
    return render(request, 'notifications/mes_notifications.html', context)


@login_required
def marquer_notification_lue(request, notif_id):
    """Vue AJAX pour marquer une notification comme lue"""
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification, 
            id=notif_id, 
            utilisateur=request.user
        )
        notification.marquer_comme_lue()
        
        # Compter les notifications restantes
        count = Notification.objects.filter(
            utilisateur=request.user,
            est_lue=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def marquer_toutes_lues(request):
    """Vue AJAX pour marquer toutes les notifications comme lues"""
    if request.method == 'POST':
        Notification.objects.filter(
            utilisateur=request.user,
            est_lue=False
        ).update(est_lue=True)
        
        return JsonResponse({
            'success': True,
            'count': 0
        })
    
    return JsonResponse({'success': False}, status=400)


