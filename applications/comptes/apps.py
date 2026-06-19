from django.apps import AppConfig


class ComptesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.comptes'
    verbose_name = "Gestion des Comptes"

    def ready(self):
        import applications.comptes.signals  # ✅ important !

