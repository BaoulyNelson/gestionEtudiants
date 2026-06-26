from django.apps import AppConfig


class DevoirsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name     = 'applications.devoirs'
    app_name = "Gestion des devoirs"

    def ready(self):
        pass  # Réservé pour les signaux si nécessaire
