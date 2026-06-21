from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('ajouter/<slug:slug>/',   views.VueAjouterCommentaire.as_view(),  name='ajouter'),
    path('supprimer/<int:pk>/',    views.VueSupprimerCommentaire.as_view(), name='supprimer'),
    path('tableau-de-bord/',       views.VueDashboardCommentaires.as_view(),name='dashboard_commentaires'),
    path('approuver/<int:pk>/',    views.VueToggleApprouver.as_view(),      name='approuver'),
]
