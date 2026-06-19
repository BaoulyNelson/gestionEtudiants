# backends.py
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()


class AuthentificationUniverselle(ModelBackend):
    """
    Authentification via email, numéro de téléphone ou numéro étudiant.
    Gère les formats haïtiens : 509XXXXXXXX, +509XXXXXXXX, 8 chiffres seuls.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        identifiant = username.strip()

        # ── Téléphone ──────────────────────────────────────────────
        if re.match(r'^\+?\d[\d\s\-]+$', identifiant):
            normalise = re.sub(r'[\s\-]', '', identifiant)

            if not normalise.startswith('+'):
                if normalise.startswith('509') and len(normalise) == 11:
                    normalise = f'+{normalise}'
                elif len(normalise) == 8:
                    # Format local haïtien sans indicatif
                    normalise = f'+509{normalise}'
                else:
                    normalise = f'+{normalise}'

            lookup = Q(numero_telephone=normalise)

        # ── Email ───────────────────────────────────────────────────
        elif '@' in identifiant:
            lookup = Q(email__iexact=identifiant)

        # ── Numéro étudiant ─────────────────────────────────────────
        else:
            lookup = Q(profil_etudiant__numero_etudiant__iexact=identifiant)

        utilisateur = UserModel.objects.filter(lookup).select_related(
            'profil_etudiant'
        ).first()

        if utilisateur and utilisateur.check_password(password) and self.user_can_authenticate(utilisateur):
            return utilisateur

        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None