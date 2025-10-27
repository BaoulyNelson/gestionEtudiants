
# ========== 3. notifications/apps.py (MODIFIER) ==========
from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        """Charger les signals au démarrage de l'application"""
        import notifications.signals


