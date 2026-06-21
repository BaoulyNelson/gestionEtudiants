from django.contrib import admin
from .models import MessageContact


@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'email', 'sujet', 'is_read', 'created_at')
    list_filter   = ('sujet', 'is_read', 'created_at')
    search_fields = ('nom', 'email', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('ip_address', 'created_at')
    date_hierarchy = 'created_at'
