# applications/portail/context_processors.py

from django.core.cache import cache
from django.utils import timezone
from .models import SiteSettings, Examen
from applications.articles.models import Categorie, Article


def site_settings(request):

    # ── SiteSettings ─────────────────────────────────────────────────────────
    site = SiteSettings.get()

    # ── App articles ──────────────────────────────────────────────────────────
    categories = cache.get("nav_categories")
    if categories is None:
        categories = list(Categorie.objects.all()[:8])
        cache.set("nav_categories", categories, 300)

    breaking = cache.get("breaking_news")
    if breaking is None:
        breaking = list(
            Article.objects.filter(
                statut="publie",
                est_breaking=True,
            ).order_by("-publie_le")[:5]
        )
        cache.set("breaking_news", breaking, 60)

    # ── Badges sidebar (étudiant uniquement) ──────────────────────────────────
    badges = {}
    user = request.user

    if user.is_authenticated and hasattr(user, 'profil_etudiant'):
        from applications.inscriptions.models import Inscription
        from applications.notes.models import Note
        from applications.devoirs.models import Devoir, Remise

        etudiant = user.profil_etudiant

        # Cours actifs
        badges['cours_count'] = Inscription.objects.filter(
            etudiant=etudiant,
            statut='INSCRIT',
        ).count()

        # Notes non encore vues (disparaît dès ouverture de "Mes Notes")
        badges['notes_count'] = Note.objects.filter(
            inscription__etudiant=etudiant,
            note_finale__isnull=False,
            est_lu=False,
        ).count()

        # Examens à venir dans les sections inscrites
        badges['examens_count'] = Examen.objects.filter(
            section_cours__inscriptions__etudiant=etudiant,
            section_cours__inscriptions__statut='INSCRIT',
            statut='a_venir',
        ).count()

        # Devoirs publiés, délai non expiré, pas encore remis
        sections_inscrites = Inscription.objects.filter(
            etudiant=etudiant,
            statut__in=['INSCRIT', 'COMPLETE'],
        ).values_list('section_cours_id', flat=True)

        devoirs_remis_ids = Remise.objects.filter(
            etudiant=etudiant,
        ).values_list('devoir_id', flat=True)

        badges['devoirs_count'] = Devoir.objects.filter(
            section_cours_id__in=sections_inscrites,
            est_publie=True,
            date_limite__gt=timezone.now(),
        ).exclude(
            id__in=devoirs_remis_ids,
        ).count()

    return {
        "site":          site,
        "nav_categories": categories,
        "breaking_news": breaking,
        "badges":        badges,
    }