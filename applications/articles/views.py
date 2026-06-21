from django.utils import timezone   # ✅ le timezone Django qui a .now()
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.core.cache import cache
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import Annonce, Article, Categorie, Evenement, Tag
from .forms import FormulaireArticle, FormulaireCategorieAdmin, FormulaireAnnonce, FormulaireEvenement
# ── Mixins de permission ──────────────────────────────────────────────────────


class EditeurRequisMixin(LoginRequiredMixin):
    login_url = "/comptes/connexion/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Connectez-vous pour acceder a cette page.")
            return self.handle_no_permission()
        if not request.user.peut_ecrire:
            raise PermissionDenied("Acces refuse.")
        return super().dispatch(request, *args, **kwargs)


class GestionnaireRequisMixin(LoginRequiredMixin):
    login_url = "/comptes/connexion/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.peut_gerer:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ── Vues publiques ────────────────────────────────────────────────────────────


class VueAccueil(ListView):
    template_name = "articles/accueil.html"
    context_object_name = "articles"

    def get_queryset(self):
        return (
            Article.objects.filter(statut="publie")
            .select_related(
                "auteur",
                "categorie",
                "auteur__profil_etudiant",
                "auteur__profil_professeur",
                "auteur__profil_admin",
            )
            .prefetch_related("tags")[:12]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cached = cache.get("accueil_ctx")
        if not cached:
            qs = Article.objects.filter(statut="publie").select_related(
                "auteur",
                "categorie",
                "auteur__profil_etudiant",
                "auteur__profil_professeur",
                "auteur__profil_admin",
            )
            cached = {
                "article_une": qs.filter(est_a_la_une=True).first(),
                "articles_une": qs.filter(est_a_la_une=True)[:4],
                "articles_recents": qs[:9],
                "articles_populaires": qs.order_by("-nombre_vues")[:5],
                "toutes_categories": list(Categorie.objects.all()[:8]),
            }
            cache.set("accueil_ctx", cached, 120)
        ctx.update(cached)
        return ctx


class VueListeArticles(ListView):
    template_name = "articles/liste_articles.html"
    context_object_name = "articles"

    def get_paginate_by(self, queryset):
        from django.conf import settings

        return settings.ARTICLES_PAR_PAGE

    def get_queryset(self):
        return (
            Article.objects.filter(statut="publie")
            .select_related(
                "auteur",
                "categorie",
                "auteur__profil_etudiant",
                "auteur__profil_professeur",
                "auteur__profil_admin",
            )
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Categorie.objects.all()
        ctx["titre_page"] = "Toutes les actualites"
        return ctx


from django.http import Http404
from django.db.models import F


class VueDetailArticle(DetailView):
    template_name = "articles/detail_articles.html"
    context_object_name = "article"

    def get_queryset(self):
        # Queryset de base sans filtre statut — le filtrage se fait dans get_object
        return Article.objects.select_related(
            "auteur",
            "categorie",
            "auteur__profil_etudiant",
            "auteur__profil_professeur",
            "auteur__profil_admin",
        ).prefetch_related("tags")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if obj.statut == "publie":
            obj.incrementer_vues()
            return obj

        # Brouillon / révision → staff ou auteur uniquement
        user = self.request.user
        if user.is_authenticated and (user.is_staff or obj.auteur == user):
            return obj  # pas d'incrément de vues pour les aperçus

        raise Http404

    def get_context_data(self, **kwargs):
        from applications.comments.forms import FormulaireCommentaire

        ctx = super().get_context_data(**kwargs)
        art = self.object

        similaires = (
            Article.objects.filter(statut="publie", categorie=art.categorie)
            .exclude(pk=art.pk)
            .select_related("auteur", "categorie")[:3]
        )
        if not similaires:
            similaires = (
                Article.objects.filter(statut="publie")
                .exclude(pk=art.pk)
                .order_by("-publie_le")[:3]
            )

        ctx["articles_similaires"] = similaires
        ctx["formulaire_commentaire"] = FormulaireCommentaire()
        ctx["commentaires"] = (
            art.commentaire_set.filter(est_approuve=True, parent__isnull=True)
            .select_related(
                "auteur",
                "auteur__profil_etudiant",
                "auteur__profil_professeur",
                "auteur__profil_admin",
            )
            .prefetch_related("replies")
        )
        ctx["articles_populaires"] = Article.objects.filter(statut="publie").order_by(
            "-nombre_vues"
        )[:5]
        return ctx


class VueCategorieArticles(ListView):
    template_name = "articles/categorie.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        self.categorie = get_object_or_404(Categorie, slug=self.kwargs["slug"])
        return Article.objects.filter(
            statut="publie", categorie=self.categorie
        ).select_related(
            "auteur",
            "categorie",
            "auteur__profil_etudiant",
            "auteur__profil_professeur",
            "auteur__profil_admin",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorie"] = self.categorie
        ctx["categories"] = Categorie.objects.all()
        return ctx


class VueTagArticles(ListView):
    template_name = "articles/tag.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return Article.objects.filter(statut="publie", tags=self.tag).select_related(
            "auteur",
            "categorie",
            "auteur__profil_etudiant",
            "auteur__profil_professeur",
            "auteur__profil_admin",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tag"] = self.tag
        return ctx


class VueRecherche(ListView):
    template_name = "articles/recherche.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()
        if self.query:
            return (
                Article.objects.filter(
                    Q(titre__icontains=self.query)
                    | Q(extrait__icontains=self.query)
                    | Q(tags__nom__icontains=self.query),
                    statut="publie",
                )
                .distinct()
                .select_related("auteur", "categorie")
            )
        return Article.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.query
        ctx["nombre_resultats"] = self.get_queryset().count()
        return ctx


# ── Tableau de bord ───────────────────────────────────────────────────────────


class VueTableauBord(EditeurRequisMixin, TemplateView):
    template_name = "dashboard/accueil.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        is_gestionnaire = user.peut_gerer
        articles = (
            Article.objects.all()
            if is_gestionnaire
            else Article.objects.filter(auteur=user)
        )
        ctx.update(
            {
                "total_articles": articles.count(),
                "articles_publies": articles.filter(statut="publie").count(),
                "articles_brouillons": articles.filter(statut="brouillon").count(),
                "articles_recents": articles.select_related("categorie").order_by(
                    "-cree_le"
                )[:5],
                "is_gestionnaire": is_gestionnaire,
                "total_categories": Categorie.objects.count(),
            }
        )
        from applications.comments.models import Commentaire

        if is_gestionnaire:
            ctx["total_commentaires"] = Commentaire.objects.count()
            ctx["commentaires_recents"] = Commentaire.objects.select_related(
                "auteur", "article"
            ).order_by("-cree_le")[:5]
        else:
            ids = articles.values_list("id", flat=True)
            ctx["total_commentaires"] = Commentaire.objects.filter(
                article_id__in=ids
            ).count()
            ctx["commentaires_recents"] = (
                Commentaire.objects.filter(article_id__in=ids)
                .select_related("auteur", "article")
                .order_by("-cree_le")[:5]
            )
        return ctx


class VueDashboardArticles(EditeurRequisMixin, ListView):
    template_name = "dashboard/articles/liste.html"
    context_object_name = "articles"
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        qs = (
            Article.objects.all()
            if user.peut_gerer
            else Article.objects.filter(auteur=user)
        )
        st = self.request.GET.get("statut")
        if st:
            qs = qs.filter(statut=st)
        return qs.select_related("auteur", "categorie").order_by("-cree_le")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statut_filtre"] = self.request.GET.get("statut", "")
        return ctx


class VueDashboardCreerArticle(EditeurRequisMixin, CreateView):
    template_name = "dashboard/articles/formulaire.html"
    form_class = FormulaireArticle
    success_url = reverse_lazy("articles:dashboard_articles")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, "Article cree avec succes !")
        cache.delete("accueil_ctx")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Erreur lors de la creation. Corrigez les erreurs ci-dessous."
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = "Creer un article"
        ctx["bouton_submit"] = "Creer l'article"
        return ctx


class VueDashboardModifierArticle(EditeurRequisMixin, UpdateView):
    template_name = "dashboard/articles/formulaire.html"
    form_class = FormulaireArticle
    success_url = reverse_lazy("articles:dashboard_articles")

    def get_queryset(self):
        user = self.request.user
        return (
            Article.objects.all()
            if user.peut_gerer
            else Article.objects.filter(auteur=user)
        )

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, "Article mis a jour avec succes !")
        cache.delete("accueil_ctx")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la modification.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = f"Modifier : {self.object.titre}"
        ctx["bouton_submit"] = "Enregistrer les modifications"
        return ctx


class VueDashboardSupprimerArticle(EditeurRequisMixin, DeleteView):
    template_name = "dashboard/articles/confirmer_suppression.html"
    success_url = reverse_lazy("articles:dashboard_articles")

    def get_queryset(self):
        user = self.request.user
        return (
            Article.objects.all()
            if user.peut_gerer
            else Article.objects.filter(auteur=user)
        )

    def form_valid(self, form):
        messages.success(self.request, "Article supprime avec succes.")
        cache.delete("accueil_ctx")
        return super().form_valid(form)


class VueDashboardCategories(GestionnaireRequisMixin, ListView):
    template_name = "dashboard/categories/liste.html"
    context_object_name = "categories"
    queryset = Categorie.objects.all()


class VueDashboardCreerCategorie(GestionnaireRequisMixin, CreateView):
    template_name = "dashboard/categories/formulaire.html"
    form_class = FormulaireCategorieAdmin
    success_url = reverse_lazy("articles:dashboard_categories")

    def form_valid(self, form):
        messages.success(self.request, "Categorie creee avec succes !")
        cache.delete("nav_categories")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = "Nouvelle categorie"
        return ctx


class VueDashboardModifierCategorie(GestionnaireRequisMixin, UpdateView):
    template_name = "dashboard/categories/formulaire.html"
    form_class = FormulaireCategorieAdmin
    queryset = Categorie.objects.all()
    success_url = reverse_lazy("articles:dashboard_categories")

    def form_valid(self, form):
        messages.success(self.request, "Categorie mise a jour !")
        cache.delete("nav_categories")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = f"Modifier : {self.object.nom}"
        return ctx


class VueDashboardSupprimerCategorie(GestionnaireRequisMixin, DeleteView):
    template_name = "dashboard/categories/confirmer_suppression.html"
    queryset = Categorie.objects.all()
    success_url = reverse_lazy("articles:dashboard_categories")

    def form_valid(self, form):
        messages.success(self.request, "Categorie supprimee.")
        cache.delete("nav_categories")
        return super().form_valid(form)

# ── Annonces ───────────────────────────────────────────────────────────────


class VueListeAnnonces(ListView):
    template_name = "articles/liste_annonces.html"
    context_object_name = "annonces"
    paginate_by = 9

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()
        qs = Annonce.objects.filter(est_active=True).order_by("-date_publication")
        if self.query:
            qs = qs.filter(
                Q(titre__icontains=self.query) | Q(contenu__icontains=self.query)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.query
        ctx["total"] = self.get_queryset().count()
        return ctx


class VueDetailAnnonce(DetailView):
    template_name = "articles/detail_annonce.html"
    context_object_name = "annonce"
    queryset = Annonce.objects.filter(est_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["annonces_recentes"] = (
            Annonce.objects.filter(est_active=True)
            .exclude(pk=self.object.pk)
            .order_by("-date_publication")[:5]
        )
        return ctx


# ── Événements ────────────────────────────────────────────────────────────


class VueListeEvenements(ListView):
    template_name = "articles/liste_evenements.html"
    context_object_name = "evenements"
    paginate_by = 9

    def get_queryset(self):
        now = timezone.now()
        self.filtre = self.request.GET.get("filtre", "tous")

        if self.filtre == "a_venir":
            qs = Evenement.objects.filter(date_debut__gt=now).order_by("date_debut")
        elif self.filtre == "en_cours":
            qs = Evenement.objects.filter(
                date_debut__lte=now, date_fin__gte=now
            ).order_by("date_debut")
        elif self.filtre == "termines":
            qs = Evenement.objects.filter(date_fin__lt=now).order_by("-date_debut")
        else:
            qs = Evenement.objects.all().order_by("date_debut")

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        ctx["filtre"] = self.filtre
        ctx["total"] = Evenement.objects.count()
        ctx["prochain"] = (
            Evenement.objects.filter(date_debut__gt=now).order_by("date_debut").first()
        )
        return ctx


class VueDetailEvenement(DetailView):
    template_name = "articles/detail_evenement.html"
    context_object_name = "evenement"
    queryset = Evenement.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["evenements_recents"] = (
            Evenement.objects.exclude(pk=self.object.pk).order_by("-date_debut")[:5]
        )
        return ctx
    
    
# ── Annonces : Tableau de bord ────────────────────────────────────────────────


class VueDashboardAnnonces(EditeurRequisMixin, ListView):
    template_name = "dashboard/annonces/dashboard_annonces_liste.html"
    context_object_name = "annonces"
    paginate_by = 15

    def get_queryset(self):
        qs = Annonce.objects.all().order_by("-date_publication")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(titre__icontains=q) | Q(contenu__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class VueDashboardCreerAnnonce(EditeurRequisMixin, CreateView):
    template_name = "dashboard/annonces/dashboard_annonces_formulaire.html"
    form_class = FormulaireAnnonce
    success_url = reverse_lazy("articles:dashboard_annonces")

    def form_valid(self, form):
        messages.success(self.request, "Annonce creee avec succes !")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Erreur lors de la creation. Corrigez les erreurs ci-dessous."
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = "Creer une annonce"
        ctx["bouton_submit"] = "Creer l'annonce"
        return ctx


class VueDashboardModifierAnnonce(EditeurRequisMixin, UpdateView):
    template_name = "dashboard/annonces/dashboard_annonces_formulaire.html"
    form_class = FormulaireAnnonce
    queryset = Annonce.objects.all()
    success_url = reverse_lazy("articles:dashboard_annonces")

    def form_valid(self, form):
        messages.success(self.request, "Annonce mise a jour avec succes !")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la modification.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = f"Modifier : {self.object.titre}"
        ctx["bouton_submit"] = "Enregistrer les modifications"
        return ctx


class VueDashboardSupprimerAnnonce(EditeurRequisMixin, DeleteView):
    template_name = "dashboard/annonces/confirmer_suppression.html"
    queryset = Annonce.objects.all()
    success_url = reverse_lazy("articles:dashboard_annonces")

    def form_valid(self, form):
        messages.success(self.request, "Annonce supprimee avec succes.")
        return super().form_valid(form)
    
    
    
    
    
    
    
    
# ── Événements : Tableau de bord ──────────────────────────────────────────────

class VueDashboardEvenements(EditeurRequisMixin, ListView):
    template_name = "dashboard/evenements/dashboard_evenements_liste.html"
    context_object_name = "evenements"
    paginate_by = 15

    def get_queryset(self):
        now = timezone.now()
        self.filtre = self.request.GET.get("filtre", "")
        qs = Evenement.objects.all().order_by("-date_debut")
        if self.filtre == "a_venir":
            qs = qs.filter(date_debut__gt=now)
        elif self.filtre == "en_cours":
            qs = qs.filter(date_debut__lte=now, date_fin__gte=now)
        elif self.filtre == "termines":
            qs = qs.filter(date_fin__lt=now)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtre"] = self.filtre
        return ctx


class VueDashboardCreerEvenement(EditeurRequisMixin, CreateView):
    template_name = "dashboard/evenements/dashboard_evenements_formulaire.html"
    form_class = FormulaireEvenement
    success_url = reverse_lazy("articles:dashboard_evenements")

    def form_valid(self, form):
        messages.success(self.request, "Evenement cree avec succes !")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Erreur lors de la creation. Corrigez les erreurs ci-dessous."
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = "Creer un evenement"
        ctx["bouton_submit"] = "Creer l'evenement"
        return ctx


class VueDashboardModifierEvenement(EditeurRequisMixin, UpdateView):
    template_name = "dashboard/evenements/dashboard_evenements_formulaire.html"
    form_class = FormulaireEvenement
    queryset = Evenement.objects.all()
    success_url = reverse_lazy("articles:dashboard_evenements")

    def form_valid(self, form):
        messages.success(self.request, "Evenement mis a jour avec succes !")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Erreur lors de la modification.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre_page"] = f"Modifier : {self.object.titre}"
        ctx["bouton_submit"] = "Enregistrer les modifications"
        return ctx


class VueDashboardSupprimerEvenement(EditeurRequisMixin, DeleteView):
    template_name = "dashboard/evenements/dashboard_evenements_confirmer_suppression.html"
    context_object_name = "evenement"
    queryset = Evenement.objects.all()
    success_url = reverse_lazy("articles:dashboard_evenements")

    def form_valid(self, form):
        messages.success(self.request, "Evenement supprime avec succes.")
        return super().form_valid(form)
    
    
# ── Gestionnaires d'erreurs ───────────────────────────────────────────────────


def erreur_404(request, exception):
    return render(request, "404.html", statut=404)


def erreur_500(request):
    return render(request, "500.html", statut=500)