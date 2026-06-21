import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()


class AuthentificationUniverselle(ModelBackend):
    """
    Authentification via email, numéro de téléphone ou numéro étudiant (CIN).

    Distinction par longueur, sans ambiguïté possible :
      - Téléphone haïtien : 8 chiffres locaux, ou 11 chiffres avec l'indicatif
        509 (avec ou sans '+').
      - Matricule étudiant (CIN / NINU) : exactement 10 chiffres.
      - Email : contient '@'.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        identifiant = username.strip()
        normalise = re.sub(r'[\s\-]', '', identifiant)

        # ── Email ───────────────────────────────────────────────────
        if '@' in identifiant:
            lookup = Q(email__iexact=identifiant)

        # ── Téléphone (8 chiffres locaux, ou 11 avec indicatif 509) ──
        elif re.fullmatch(r'\+?509\d{8}', normalise) or re.fullmatch(r'\d{8}', normalise):
            if not normalise.startswith('+'):
                if normalise.startswith('509') and len(normalise) == 11:
                    normalise = f'+{normalise}'
                elif len(normalise) == 8:
                    normalise = f'+509{normalise}'
            lookup = Q(numero_telephone=normalise)

        # ── Numéro étudiant / CIN (10 chiffres, ou tout autre format) ─
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