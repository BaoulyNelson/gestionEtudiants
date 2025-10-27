import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    """
    Permet la connexion avec email OU numéro de téléphone.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None
        username = username.strip()

        # Si c’est un numéro, on le nettoie
        if re.match(r'^\+?\d+$', username):
            username = username.replace(' ', '')
            if username.startswith('509'):
                normalized = f'+{username}'
            elif username.startswith('+509'):
                normalized = username
            elif len(username) == 8:
                normalized = f'+509{username}'
            else:
                normalized = username
            lookup = Q(phone_number__iexact=normalized)
        else:
            lookup = Q(email__iexact=username)

        try:
            user = UserModel.objects.get(lookup)
        except UserModel.DoesNotExist:
            return None

        if user and user.check_password(password):
            return user
        return None
