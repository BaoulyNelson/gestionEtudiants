from django.views.generic import CreateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views import View
from .models import Commentaire
from .forms import FormulaireCommentaire
from applications.articles.models import Article
from applications.articles.views import GestionnaireRequisMixin


class VueAjouterCommentaire(LoginRequiredMixin, CreateView):
    model      = Commentaire
    form_class = FormulaireCommentaire
    login_url  = '/comptes/connexion/'

    def form_valid(self, form):
        article = get_object_or_404(Article, slug=self.kwargs['slug'], status='publie')
        c = form.save(commit=False)
        c.auteur  = self.request.user
        c.article = article
        c.save()
        messages.success(self.request, 'Votre commentaire a ete publie.')
        return redirect(
            reverse('articles:detail', kwargs={'slug': article.slug}) + '#commentaires'
        )

    def form_invalid(self, form):
        messages.error(self.request, 'Erreur lors de la publication du commentaire.')
        return redirect('articles:detail', slug=self.kwargs['slug'])


class VueSupprimerCommentaire(LoginRequiredMixin, DeleteView):
    model     = Commentaire
    login_url = '/comptes/connexion/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        commentaire = get_object_or_404(Commentaire, pk=kwargs['pk'])
        is_owner   = commentaire.auteur == request.user
        is_manager = request.user.is_staff or (
            hasattr(request.user, 'userprofile') and request.user.userprofile.can_manage
        )
        if not (is_owner or is_manager):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, 'Commentaire supprime.')
        return reverse('articles:detail', kwargs={'slug': self.object.article.slug})


class VueDashboardCommentaires(GestionnaireRequisMixin, ListView):
    template_name       = 'dashboard/commentaires/liste.html'
    context_object_name = 'commentaires'
    paginate_by         = 20

    def get_queryset(self):
        return Commentaire.objects.select_related(
            'auteur', 'article', 'auteur__profil_etudiant', 'auteur__profil_professeur', 'auteur__profil_admin'
        ).order_by('-cree_le')


class VueToggleApprouver(GestionnaireRequisMixin, View):
    def post(self, request, pk):
        c = get_object_or_404(Commentaire, pk=pk)
        c.est_approuved= not c.est_approuved
        c.save()
        etat = 'approuve' if c.est_approuved else 'masque'
        messages.success(request, f'Commentaire {etat}.')
        return redirect('comments:dashboard_commentaires')
