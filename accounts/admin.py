from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Professor, Admin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'phone_number', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de connexion', {
            'fields': ('email', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone_number', 'address', 
                      'date_of_birth', 'profile_picture')
        }),
        ('Rôle et permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 
                      'must_change_password')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 
                      'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_number', 'get_full_name', 'department', 'current_year', 'enrollment_date']
    list_filter = ['department', 'current_year']
    search_fields = ['student_number', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nom complet'


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ['professor_id', 'get_full_name', 'department', 'specialization', 'hire_date']
    list_filter = ['department']
    search_fields = ['professor_id', 'user__first_name', 'user__last_name', 'specialization']
    raw_id_fields = ['user']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nom complet'


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ['admin_id', 'get_full_name', 'position']
    search_fields = ['admin_id', 'user__first_name', 'user__last_name', 'position']
    raw_id_fields = ['user']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nom complet'
    
    
    
    
    
    
    
    
    
    
    
    
    
