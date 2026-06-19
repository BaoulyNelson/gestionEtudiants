from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from applications.notifications.models import Notification


def _envoyer_notification_note(etudiant, note, anciennes_valeurs=None):
    """
    Envoie une notification à l'étudiant concernant une note créée ou modifiée.
    """

    utilisateur = etudiant.utilisateur

    cours = note.inscription.section_cours.cours

    # ─────────────────────────────
    # CAS 1 : nouvelle note
    # ─────────────────────────────
    if not anciennes_valeurs:
        type_notif = 'note_publiee'
        titre = f"Votre note en {cours.nom} a été publiée"

        message = (
            f"La note finale {note.note_finale}/100 "
            f"({note.mention}) a été enregistrée pour le cours {cours.code}."
        )

        ancienne_note = None

    # ─────────────────────────────
    # CAS 2 : modification
    # ─────────────────────────────
    else:
        type_notif = 'note_modifiee'
        titre = f"Votre note en {cours.nom} a été modifiée"

        noms_champs = {
            'examen_mi_parcours': 'Examen mi-parcours',
            'examen_final': 'Examen final',
            'travaux': 'Travaux',
            'participation': 'Participation',
            'projet': 'Projet',
            'note_finale': 'Note finale',
            'mention': 'Mention',
        }

        lignes = []
        for champ, vals in anciennes_valeurs.items():
            ancienne = vals.get('ancienne')
            nouvelle = vals.get('nouvelle')

            if ancienne != nouvelle:
                nom = noms_champs.get(champ, champ)
                lignes.append(f"• {nom}: {ancienne} → {nouvelle}")

        message = "Vos notes ont été mises à jour :\n" + "\n".join(lignes)

        ancienne_note = anciennes_valeurs.get('note_finale', {}).get('ancienne')

    # ─────────────────────────────
    # Notification DB
    # ─────────────────────────────
    Notification.objects.create(
        utilisateur=utilisateur,
        type_notification=type_notif,
        titre=titre,
        message=message,
        lien='/notes/'
    )

    # ─────────────────────────────
    # Email
    # ─────────────────────────────
    contexte_email = {
        'utilisateur': utilisateur,
        'cours': cours.nom,
        'code_cours': cours.code,
        'note_finale': note.note_finale,
        'note_lettre': note.mention,
        'ancienne_note': ancienne_note,
        'commentaires': note.commentaires,
        'professeur': note.note_par.utilisateur.get_full_name() if note.note_par else 'N/A',
        'changements': anciennes_valeurs,
    }

    try:
        html = render_to_string('email/notification_note.html', contexte_email)
        text = strip_tags(html)

        send_mail(
            titre,
            text,
            'noreply@fasch.edu',
            [utilisateur.email],
            html_message=html,
            fail_silently=True,
        )

    except Exception as e:
        print(f"❌ Erreur email: {e}")