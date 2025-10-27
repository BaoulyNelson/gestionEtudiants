# ========== enrollments/admin.py - REMPLACER COMPLÈTEMENT ==========
from django.contrib import admin
from django.utils.html import format_html
from .models import Enrollment, EnrollmentHistory


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student_display', 'course_section_display', 'status_badge', 
                    'enrollment_date', 'quick_actions']
    list_filter = ['status', 'course_section__session', 'course_section__semester', 
                   'course_section__year', 'enrollment_date']
    search_fields = ['student__student_number', 'student__user__first_name', 
                    'student__user__last_name', 'course_section__course__code']
    raw_id_fields = ['student', 'course_section']
    date_hierarchy = 'enrollment_date'
    ordering = ['-enrollment_date']
    list_per_page = 20
    
    fieldsets = (
        ('📝 Inscription', {
            'fields': ('student', 'course_section', 'status')
        }),
        ('📅 Dates', {
            'fields': ('enrollment_date', 'drop_date')
        }),
    )
    
    readonly_fields = ['enrollment_date']
    
    actions = ['mark_as_completed', 'mark_as_dropped']
    
    def student_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.student.student_number,
            obj.student.user.get_full_name()
        )
    student_display.short_description = 'Étudiant'
    
    def course_section_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>Section {}</small>',
            obj.course_section.course.code,
            obj.course_section.section_number
        )
    course_section_display.short_description = 'Cours'
    
    def status_badge(self, obj):
        colors = {
            'ENROLLED': 'green',
            'DROPPED': 'red',
            'COMPLETED': 'blue',
            'FAILED': 'darkred'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def quick_actions(self, obj):
        return format_html(
            '<a class="button" href="/admin/grades/grade/add/?enrollment={}">➕ Ajouter note</a>',
            obj.id
        )
    quick_actions.short_description = 'Actions'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} inscription(s) marquée(s) comme complétée(s).')
    mark_as_completed.short_description = "✓ Marquer comme complété"
    
    def mark_as_dropped(self, request, queryset):
        from django.utils import timezone
        for enrollment in queryset:
            enrollment.status = 'DROPPED'
            enrollment.drop_date = timezone.now()
            enrollment.save()
        self.message_user(request, f'{queryset.count()} inscription(s) abandonnée(s).')
    mark_as_dropped.short_description = "✗ Marquer comme abandonné"


@admin.register(EnrollmentHistory)
class EnrollmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'previous_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['previous_status', 'new_status', 'changed_at']
    search_fields = ['enrollment__student__student_number']
    raw_id_fields = ['enrollment', 'changed_by']
    date_hierarchy = 'changed_at'
    ordering = ['-changed_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
