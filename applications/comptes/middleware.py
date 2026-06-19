from django.shortcuts import redirect
from django.urls import reverse


class ControleurChangementMotDePasse:
    """Middleware pour forcer le changement de mot de passe temporaire"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.urls_exemptees = [
            reverse('comptes:changer_mot_de_passe'),
            reverse('comptes:deconnexion'),
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.doit_changer_mot_de_passe:
                if not any(request.path.startswith(url) for url in self.urls_exemptees):
                    return redirect('comptes:changer_mot_de_passe')
        response = self.get_response(request)
        return response