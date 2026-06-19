# urls.py — VERSION FINALE

from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('',
         views.ListArticles.as_view(),
         name='liste_articles'),

    path('publications/',
         views.ListPublications.as_view(),
         name='liste_publications'),

    path('publications/<slug:slug>/',
         views.DetailPublication.as_view(),
         name='detail_publication'),
]