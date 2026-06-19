from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from applications.departements.models import Departement
from applications.cours.models import Cours


def liste_departements(request):
    """
    Page principale des départements.
    Le slug actif vient du GET (?dept=psychologie),
    par défaut le premier département actif.
    """
    departements = Departement.objects.filter(est_actif=True).order_by('ordre', 'nom')

    slug_actif = request.GET.get('dept', '')
    dept_actif = None

    if slug_actif:
        dept_actif = departements.filter(slug=slug_actif).first()

    if not dept_actif and departements.exists():
        dept_actif = departements.first()
        slug_actif = dept_actif.slug if dept_actif else ''

    return render(request, 'departements/liste.html', {
        'departements': departements,
        'dept_actif':   dept_actif,
        'slug_actif':   slug_actif,
    })


@login_required
def cours_par_departement(request, id_departement):
    departement = get_object_or_404(Departement, pk=id_departement)
    cours = Cours.objects.filter(departement=departement)
    return render(request, 'cours/liste_par_departement.html', {
        'departement': departement,
        'cours':       cours,
    })