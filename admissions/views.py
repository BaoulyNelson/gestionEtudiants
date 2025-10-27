from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CandidatureForm
from .models import Candidature, Ambassadeur, FAQ , Statistique
from departments.models import Department
from django.contrib.auth.decorators import login_required



# Vue basée sur une fonction
@login_required
def soumettre_candidature(request):
    if request.method == 'POST':
        form = CandidatureForm(request.POST)
        action = request.POST.get('action')
        
        if form.is_valid():
            candidature = form.save(commit=False)
            
            # Déterminer le statut selon l'action
            if action == 'brouillon':
                candidature.statut = 'brouillon'
                messages.success(request, '✓ Votre brouillon a été sauvegardé avec succès.')
            else:  # soumission
                candidature.statut = 'soumis'
                messages.success(request, '✓ Votre candidature a été soumise avec succès! Vous recevrez une confirmation par email.')
            
            candidature.save()
            return redirect('candidature_confirmation', pk=candidature.pk)
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CandidatureForm()
    
    # Données pour la page complète
    context = {
        'form': form,
        'programmes': Department.objects.all(),
        'statistiques': Statistique.objects.all(),
        'ambassadeurs': Ambassadeur.objects.all()[:3],
        'faqs': FAQ.objects.all(),
    }
    
    return render(request, 'admissions/confirmations.html', context)

@login_required
# Ou Vue basée sur une classe (alternative)
class CandidatureCreateView(CreateView):
    model = Candidature
    form_class = CandidatureForm
    template_name = 'home.html'
    success_url = reverse_lazy('candidature_confirmation')
    
    def form_valid(self, form):
        action = self.request.POST.get('action')
        candidature = form.save(commit=False)
        
        if action == 'brouillon':
            candidature.statut = 'brouillon'
            messages.success(self.request, '✓ Votre brouillon a été sauvegardé.')
        else:
            candidature.statut = 'soumis'
            messages.success(self.request, '✓ Candidature soumise avec succès!')
        
        candidature.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programmes'] = Department.objects.all()
        context['statistiques'] = Statistique.objects.all()
        context['ambassadeurs'] = Ambassadeur.objects.all()[:3]
        context['faqs'] = FAQ.objects.all()
        return context


# Vue de confirmation
def candidature_confirmation(request, pk):
    candidature = Candidature.objects.get(pk=pk)
    return render(request, 'admission/confirmation.html', {'candidature': candidature})



def conditions_admission(request):
    """
    Affiche les conditions d'admission à la FASCH.
    """
    return render(request, 'admissions/conditions_admission.html')


def politique_confidentialite(request):
    """
    Affiche les politique_confidentialites à la FASCH.
    """
    return render(request, 'admissions/politique_confidentialite.html')

@login_required
def admission_center(request):
    """
    Centre d'admission — affiche le formulaire de candidature et
    les données associées (programmes, ambassadeurs, FAQ, etc.)
    """
    if request.method == 'POST':
        form = CandidatureForm(request.POST)
        action = request.POST.get('action')

        if form.is_valid():
            candidature = form.save(commit=False)

            # Déterminer le statut selon le bouton cliqué
            if action == 'brouillon':
                candidature.statut = 'brouillon'
                messages.success(request, '✓ Votre brouillon a été sauvegardé avec succès.')
            else:
                candidature.statut = 'soumis'
                messages.success(request, '✓ Votre candidature a été soumise avec succès! Vous recevrez une confirmation par email.')

            candidature.save()
            return redirect('admissions:candidature_confirmation', pk=candidature.pk)
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = CandidatureForm()

    # Données dynamiques pour le template
    context = {
        'form': form,
        'programmes': Department.objects.all(),
        'statistiques': Statistique.objects.all(),
        'ambassadeurs': Ambassadeur.objects.all()[:3],
        'faqs': FAQ.objects.all(),
    }

    return render(request, 'admissions/list.html', context)
