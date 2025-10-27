# ========== notifications/utils.py (AMÉLIORÉ) ==========
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from accounts.models import Student
from .models import Notification


def _envoyer_notification_note(etudiant, note, anciennes_valeurs=None):
    """
    Envoie une notification à l'étudiant concernant sa note.

    :param etudiant: Student ou User
    :param note: instance de Grade
    :param anciennes_valeurs: dict contenant les anciennes valeurs des composantes de la note
                              Format: {'champ': {'ancienne': val1, 'nouvelle': val2}}
    """
    # Récupérer l'utilisateur lié à l'étudiant
    utilisateur = etudiant.user if hasattr(etudiant, 'user') else etudiant

    cours = note.enrollment.course_section.course

    # Déterminer si la note est nouvelle ou modifiée
    if not anciennes_valeurs or len(anciennes_valeurs) == 0:
        type_notif = 'note_publiee'
        titre = f"Votre note en {cours.name} a été publiée"
        message = f"La note finale {note.final_grade}/100 ({note.letter_grade}) a été enregistrée pour le cours {cours.code}."
        ancienne_note = None
    else:
        type_notif = 'note_modifiee'
        titre = f"Votre note en {cours.name} a été modifiée"
        
        # Créer un message détaillé des changements
        lignes = []
        for champ, vals in anciennes_valeurs.items():
            ancienne = vals['ancienne']
            nouvelle = vals['nouvelle']
            
            # Traduire les noms de champs en français
            noms_champs = {
                'midterm_exam': 'Examen mi-parcours',
                'final_exam': 'Examen final',
                'assignments': 'Travaux/Devoirs',
                'participation': 'Participation',
                'project': 'Projet',
                'final_grade': 'Note finale',
                'letter_grade': 'Note lettre',
            }
            nom_affiche = noms_champs.get(champ, champ.replace('_', ' ').capitalize())
            
            if ancienne is not None and nouvelle is not None:
                lignes.append(f"• {nom_affiche}: {ancienne} → {nouvelle}")
            elif nouvelle is not None:
                lignes.append(f"• {nom_affiche}: {nouvelle} (nouvelle)")
        
        message = "Vos notes ont été mises à jour:\n" + "\n".join(lignes)
        
        # Si la note finale a changé, on peut l'afficher dans l'email
        ancienne_note = (
            anciennes_valeurs.get('final_grade', {}).get('ancienne') 
            if 'final_grade' in anciennes_valeurs 
            else None
        )

    # Créer la notification dans la base
    Notification.objects.create(
        utilisateur=utilisateur,
        type_notification=type_notif,
        titre=titre,
        message=message,
        lien='/grades/'  # Lien vers la page des notes
    )

    # Préparer le contexte pour le template email
    contexte_email = {
        'utilisateur': utilisateur,
        'cours': cours.name,
        'code_cours': cours.code,
        'note_finale': note.final_grade,
        'note_lettre': note.letter_grade,
        'ancienne_note': ancienne_note,
        'est_reussi': note.is_passing(),
        'commentaires': note.comments,
        'professeur': note.graded_by.user.get_full_name() if note.graded_by else 'N/A',
        'changements': anciennes_valeurs,  # Pour afficher tous les détails dans l'email
    }

    # Envoi de l'email
    try:
        corps_html = render_to_string('email/notification_note.html', contexte_email)
        corps_texte = strip_tags(corps_html)
        send_mail(
            titre,
            corps_texte,
            'noreply@fasch.edu',
            [utilisateur.email],
            html_message=corps_html,
            fail_silently=True,
        )
        print(f"✅ Notification envoyée à {utilisateur.email} pour {cours.code}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")
