from django.conf import settings
from django.core.cache import cache
from .models import Categorie, Article


def site_context(request):
    categories = cache.get("nav_categories")
    if not categories:
        categories = list(Categorie.objects.all()[:8])
        cache.set("nav_categories", categories, 300)

    breaking = cache.get("breaking_news")
    if not breaking:
        breaking = list(
            Article.objects.filter(status="publie", est_breaking=True).order_by(
                "-publie_le"
            )[:5]
        )
        cache.set("breaking_news", breaking, 60)

    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "nav_categories": categories,
        "breaking_news": breaking,
    }
