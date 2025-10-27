# ========== notifications/urls.py (METTRE À JOUR) ==========
from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path('', views.mes_notifications, name='mes_notifications'),
    path('marquer-lue/<int:notif_id>/', views.marquer_notification_lue, name='marquer_lue'),
    path('marquer-toutes-lues/', views.marquer_toutes_lues, name='marquer_toutes_lues'),
]
