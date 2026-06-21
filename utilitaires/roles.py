def est_professeur(user):
    """Vérifie si l'utilisateur est un professeur ou superuser"""
    return user.is_authenticated and (user.is_superuser or user.est_professeur())


def est_etudiant(user):
    """Vérifie si l'utilisateur est un étudiant"""
    return user.is_authenticated and user.est_etudiant()


def est_administrateur(user):
    """Vérifie si l'utilisateur est admin ou superuser"""
    return user.is_authenticated and (user.is_superuser or user.est_administrateur())


def est_professeur_ou_admin(user):
    """Vérifie si l'utilisateur peut gérer les examens (prof ou admin)"""
    return user.is_authenticated and (
        user.is_superuser or
        user.est_professeur() or
        user.est_administrateur()
    )