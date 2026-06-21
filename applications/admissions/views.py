from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CandidatureForm
from .models import Candidature, Ambassadeur, FAQ , Statistique
from applications.departements.models import Departement
from django.contrib.auth.decorators import login_required



# Vue de confirmation
def candidature_confirmation(request, pk):
    candidature = get_object_or_404(Candidature, pk=pk)
    return render(request, 'admissions/confirmation.html', {'candidature': candidature})



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
def centre_admissions(request):
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
        'programmes': Departement.objects.all(),
        'statistiques': Statistique.objects.all(),
        'ambassadeurs': Ambassadeur.objects.all()[:3],
        'faqs': FAQ.objects.all(),
    }

    return render(request, 'admissions/list.html', context)