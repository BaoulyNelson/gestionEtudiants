from django.shortcuts import redirect
from django.urls import reverse

class PasswordChangeMiddleware:
    """Middleware pour forcer le changement de mot de passe temporaire"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs exemptées de la redirection
        self.exempt_urls = [
            reverse('accounts:change_password'),
            reverse('accounts:logout'),
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Vérifier si l'utilisateur doit changer son mot de passe
            if request.user.must_change_password:
                # Vérifier si l'URL actuelle n'est pas exemptée
                if not any(request.path.startswith(url) for url in self.exempt_urls):
                    return redirect('accounts:change_password')
        
        response = self.get_response(request)
        return response