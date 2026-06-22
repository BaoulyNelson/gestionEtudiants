"""
URL configuration for fasch_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from applications.comptes.views import tableau_bord
from applications.portail.views import vue_accueil


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', vue_accueil, name='accueil'),  # 👈 AJOUT IMPORTANT

    # Accueil
    path('tableau-de-bord/', tableau_bord, name='tableau_de_bord'),

    # Applications
    path('comptes/', include('applications.comptes.urls')),
    path('cours/', include('applications.cours.urls')),
    path('inscriptions/', include('applications.inscriptions.urls')),
    path('notes/', include('applications.notes.urls')),
    path('portail/', include('applications.portail.urls')),
    path('departements/', include('applications.departements.urls')),
    path('articles/', include('applications.articles.urls')),
    path('notifications/', include('applications.notifications.urls')),
    path('contact/', include('applications.contact.urls')),
    path('commentaires/', include('applications.comments.urls')),
]

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)