# applications/portail/context_processors.py

from django.core.cache import cache
from .models import SiteSettings, Examen
from applications.articles.models import Categorie, Article


def site_settings(request):
    # --- SiteSettings (inchangé) ---
    site = SiteSettings.get()

    # --- App articles ---
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

    # --- Badges sidebar ---
    badges = {}
    user = request.user
    if user.is_authenticated and hasattr(user, 'profil_etudiant'):
        from applications.inscriptions.models import Inscription
        from applications.notes.models import Note

        etudiant = user.profil_etudiant
        badges['cours_count'] = Inscription.objects.filter(
            etudiant=etudiant,
            statut='INSCRIT',
        ).count()
        badges['notes_count'] = Note.objects.filter(
            inscription__etudiant=etudiant,
            note_finale__isnull=False,
        ).count()
        badges['examens_count'] = Examen.objects.filter(
            section_cours__inscriptions__etudiant=etudiant,
            section_cours__inscriptions__statut='INSCRIT',
            statut='a_venir',
        ).count()

    return {
        "site": site,
        "nav_categories": categories,
        "breaking_news": breaking,
        "badges": badges,
    }