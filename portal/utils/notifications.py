from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from portal.models import Notification

def envoyer_notification(utilisateur, type_notif, titre, message, lien=''):
    """
    Fonction générique pour envoyer une notification (et email facultatif)
    """
    Notification.objects.create(
        utilisateur=utilisateur,
        type_notification=type_notif,
        titre=titre,
        message=message,
        lien=lien
    )

    try:
        contexte_email = {'titre': titre, 'message': message, 'lien': lien}
        corps_html = render_to_string('email/notification_generale.html', contexte_email)
        corps_texte = strip_tags(corps_html)
        send_mail(
            titre,
            corps_texte,
            'noreply@gestionnotes.fr',
            [utilisateur.email],
            html_message=corps_html,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
