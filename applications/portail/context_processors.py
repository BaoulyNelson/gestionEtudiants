# context_processors.py (dans la même app)

from .models import SiteSettings

def site_settings(request):
    return {'site': SiteSettings.get()}