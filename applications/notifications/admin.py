from .models import Notification
from django.contrib import admin


# ==============================
# 🔹 Admin Notification
# ==============================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'utilisateur', 'type_notification', 'est_lue', 'date_creation', 'date_lecture')
    list_filter = ('type_notification', 'est_lue', 'date_creation')
    search_fields = ('titre', 'message', 'utilisateur__username', 'utilisateur__first_name', 'utilisateur__last_name')
    ordering = ('-date_creation',)
    readonly_fields = ('date_creation', 'date_lecture')
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Notification', {
            'fields': ('utilisateur', 'type_notification', 'titre', 'message', 'lien')
        }),
        ('Statut', {
            'fields': ('est_lue', 'date_creation', 'date_lecture')
        }),
    )
    
    actions = ['marquer_comme_lues']
    
    def marquer_comme_lues(self, request, queryset):
        """Action pour marquer plusieurs notifications comme lues"""
        count = 0
        for notification in queryset:
            if not notification.est_lue:
                notification.marquer_comme_lue()
                count += 1
        self.message_user(request, f"{count} notification(s) marquée(s) comme lue(s).")
    marquer_comme_lues.short_description = "Marquer comme lues"
