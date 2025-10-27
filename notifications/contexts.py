# ========== 1. notifications/contexts.py (CRÉER CE FICHIER) ==========
from notifications.models import Notification

def notifications_context(request):
    """Ajouter les notifications non lues dans tous les templates"""
    if request.user.is_authenticated:
        notifications_non_lues = Notification.objects.filter(
            utilisateur=request.user,
            est_lue=False
        )
        return {
            'notifications_non_lues': notifications_non_lues,
        }
    return {
        'notifications_non_lues': None,
    }


# ========== 1. Dans votre context_processor (contexts.py ou similar) ==========