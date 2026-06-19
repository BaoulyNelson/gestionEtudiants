# views.py — VERSION FINALE PROPRE

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Article, Publication, MetriqueRecherche, Partenariat
from applications.departements.models import Departement


# ── Liste des articles (simple) ─────────────────────────────────────────────
class ListArticles(View):
    def get(self, request):
        articles = Article.objects.filter(est_active=True).order_by('-date_publication')
        return render(request, 'articles/liste_articles.html', {'articles': articles})


# ── Liste des publications (avec filtres + tout le contexte) ────────────────
class ListPublications(View):
    def get(self, request):
        q           = request.GET.get('q', '').strip()
        type_pub    = request.GET.get('type', '')
        annee       = request.GET.get('annee', '')
        langue      = request.GET.get('langue', '')
        departement = request.GET.get('departement', '')

        archives = Publication.objects.filter(est_actif=True).select_related('departement')

        if q:
            archives = archives.filter(
                Q(titre__icontains=q) |
                Q(auteurs_texte__icontains=q) |
                Q(resume__icontains=q)
            )
        if type_pub:
            archives = archives.filter(type_publication=type_pub)
        if annee:
            if annee == 'older':
                archives = archives.filter(annee_publication__lt=2022)
            else:
                archives = archives.filter(annee_publication=int(annee))
        if langue:
            archives = archives.filter(langue=langue)
        if departement:
            archives = archives.filter(departement__slug=departement)

        paginator     = Paginator(archives, 10)
        archives_page = paginator.get_page(request.GET.get('page', 1))

        context = {
            # Filtres actifs (pour préremplir les selects)
            'q':           q,
            'type_pub':    type_pub,
            'annee':       annee,
            'langue':      langue,
            'departement': departement,

            # Options des selects (dynamiques depuis la BDD/modèle)
            'departements':       Departement.objects.filter(est_actif=True).order_by('nom'),
            'types_publication':  Publication.CHOIX_TYPE,
            'langues':            Publication.CHOIX_LANGUE,
            'annees_disponibles': (
                Publication.objects
                .filter(est_actif=True, annee_publication__isnull=False)
                .values_list('annee_publication', flat=True)
                .distinct()
                .order_by('-annee_publication')
            ),

            # Résultats paginés
            'archives': archives_page,
            'total':    paginator.count,

            # Sections fixes de la page
            'metriques':             MetriqueRecherche.objects.filter(est_actif=True),
            'vedettes':              Publication.objects.filter(est_actif=True, est_vedette=True).select_related('departement')[:3],
            'recherches_etudiantes': Publication.objects.filter(est_actif=True, type_publication='etudiant').order_by('-date_publication')[:2],
            'partenariats':          Partenariat.objects.filter(est_actif=True),
        }
        return render(request, 'articles/liste_publications.html', context)


# ── Détail d'une publication ────────────────────────────────────────────────
class DetailPublication(View):
    def get(self, request, slug):
        publication = get_object_or_404(Publication, slug=slug, est_actif=True)
        publication.incrementer_vues()
        return render(request, 'articles/detail_publication.html', {'publication': publication})