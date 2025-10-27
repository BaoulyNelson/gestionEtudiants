# ========== departments/admin.py - REMPLACER COMPLÈTEMENT ==========
from django.contrib import admin
from django.utils.html import format_html
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'head_display', 'students_count', 'professors_count']
    search_fields = ['code', 'name']
    list_filter = ['code']
    raw_id_fields = ['head_of_department']
    
    fieldsets = (
        ('📚 Informations principales', {
            'fields': ('code', 'name', 'description')
        }),
        ('👔 Gestion', {
            'fields': ('head_of_department',)
        }),
    )
    
    def head_display(self, obj):
        if obj.head_of_department:
            return obj.head_of_department.user.get_full_name()
        return format_html('<span style="color: gray;">Non assigné</span>')
    head_display.short_description = 'Chef de département'
    
    def students_count(self, obj):
        count = obj.get_total_students()
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; border-radius: 3px;">{} étudiant(s)</span>',
            count
        )
    students_count.short_description = 'Étudiants'
    
    def professors_count(self, obj):
        count = obj.get_total_professors()
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">{} prof(s)</span>',
            count
        )
    professors_count.short_description = 'Professeurs'






