def is_professor(user):
    """Vérifie si l'utilisateur est un professeur"""
    return user.is_authenticated and user.is_professor()


def is_student(user):
    """Vérifie si l'utilisateur est un étudiant"""
    return user.is_authenticated and user.is_student()


def is_admin(user):
    """Vérifie si l'utilisateur est admin ou superuser"""
    return user.is_authenticated and user.is_admin_user()