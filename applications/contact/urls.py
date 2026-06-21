from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('',              views.VueContact.as_view(),          name='contact'),
    path('succes/',       views.VueContactSucces.as_view(),    name='succes'),
    path('tableau-de-bord/messages/',
         views.VueDashboardMessages.as_view(), name='dashboard_messages'),
    path('tableau-de-bord/messages/<int:pk>/',
         views.VueLireMessage.as_view(), name='dashboard_lire_message'),
]
