
# ========== grades/admin.py - REMPLACER COMPLÈTEMENT ==========
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count, Q
from .models import Grade, GradeHistory, Transcript


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student_info', 'course_info', 'grade_components', 
                    'final_grade_display', 'letter_grade_badge', 'graded_by']
    list_filter = ['letter_grade', 'enrollment__course_section__course__department', 
                   'updated_at']
    search_fields = ['enrollment__student__student_number', 
                    'enrollment__student__user__first_name',
                    'enrollment__student__user__last_name',
                    'enrollment__course_section__course__code']
    raw_id_fields = ['enrollment', 'graded_by']
    ordering = ['-updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('📝 Inscription', {
            'fields': ('enrollment',)
        }),
        ('📊 Composantes de la note', {
            'fields': ('midterm_exam', 'final_exam', 'assignments', 
                      'participation', 'project'),
            'description': 'Pondérations: Mi-parcours 25%, Final 35%, Travaux 20%, Participation 10%, Projet 10%'
        }),
        ('🎯 Résultat final', {
            'fields': ('final_grade', 'letter_grade')
        }),
        ('💬 Informations supplémentaires', {
            'fields': ('comments', 'graded_by')
        }),
    )
    
    readonly_fields = ['final_grade', 'letter_grade']
    
    actions = ['recalculate_grades', 'export_grades']
    
    def student_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.enrollment.student.student_number,
            obj.enrollment.student.user.get_full_name()
        )
    student_info.short_description = 'Étudiant'
    
    def course_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>Section {}</small>',
            obj.enrollment.course_section.course.code,
            obj.enrollment.course_section.section_number
        )
    course_info.short_description = 'Cours'
    
    def grade_components(self, obj):
        components = []
        if obj.midterm_exam: components.append(f'📝 {obj.midterm_exam}')
        if obj.final_exam: components.append(f'📄 {obj.final_exam}')
        if obj.assignments: components.append(f'📚 {obj.assignments}')
        if obj.participation: components.append(f'🗣️ {obj.participation}')
        if obj.project: components.append(f'🎯 {obj.project}')
        return format_html('<br>'.join(components) if components else '-')
    grade_components.short_description = 'Composantes'
    
    def final_grade_display(self, obj):
        if obj.final_grade:
            color = 'green' if float(obj.final_grade) >= 60 else 'red'
            return format_html(
                '<span style="color: {}; font-size: 18px; font-weight: bold;">{}</span>',
                color, obj.final_grade
            )
        return '-'
    final_grade_display.short_description = 'Note finale'
    
    def letter_grade_badge(self, obj):
        if obj.letter_grade:
            colors = {
                'A': '#28a745',
                'B': '#007bff',
                'C': '#17a2b8',
                'D': '#ffc107',
                'F': '#dc3545'
            }
            return format_html(
                '<span style="background-color: {}; color: white; padding: 5px 15px; border-radius: 3px; font-size: 16px; font-weight: bold;">{}</span>',
                colors.get(obj.letter_grade, 'gray'),
                obj.letter_grade
            )
        return '-'
    letter_grade_badge.short_description = 'Lettre'
    
    def recalculate_grades(self, request, queryset):
        for grade in queryset:
            grade.save()  # Cela déclenchera le calcul automatique
        self.message_user(request, f'{queryset.count()} note(s) recalculée(s).')
    recalculate_grades.short_description = "🔄 Recalculer les notes"


@admin.register(GradeHistory)
class GradeHistoryAdmin(admin.ModelAdmin):
    list_display = ['grade', 'component', 'old_value', 'new_value', 
                    'modified_by', 'modified_at']
    list_filter = ['component', 'modified_at']
    search_fields = ['grade__enrollment__student__student_number']
    raw_id_fields = ['grade', 'modified_by']
    date_hierarchy = 'modified_at'
    ordering = ['-modified_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


from django.contrib import admin
from django.utils.html import format_html
from .models import Transcript


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'period_display',
        'gpa_display',
        'credits_display',
        'generated_at'
    ]
    
    list_filter = [
        'year',
        'semester',
        'generated_at'
    ]
    
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__student_number'
    ]
    
    readonly_fields = [
        'generated_at',
        'gpa',
        'total_credits_attempted',
        'total_credits_earned',
        'gpa_breakdown'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('student', 'semester', 'year')
        }),
        ('Statistiques', {
            'fields': (
                'gpa',
                'total_credits_attempted',
                'total_credits_earned',
                'gpa_breakdown'
            )
        }),
        ('Métadonnées', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_gpa']
    
    def period_display(self, obj):
        """Affiche la période (semestre + année)"""
        return f"{obj.semester} {obj.year}"
    period_display.short_description = 'Période'
    period_display.admin_order_field = 'year'
    
    def gpa_display(self, obj):
        """Affiche le GPA avec code couleur"""
        if obj.gpa is None:
            return format_html(
                '<span style="color: gray;">N/A</span>'
            )
        
        # Code couleur selon le GPA
        if obj.gpa >= 3.5:
            color = 'green'
        elif obj.gpa >= 3.0:
            color = 'blue'
        elif obj.gpa >= 2.0:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<strong style="color: {};">{:.2f}</strong>',
            color,
            obj.gpa
        )
    gpa_display.short_description = 'GPA'
    gpa_display.admin_order_field = 'gpa'
    
    def credits_display(self, obj):
        """Affiche les crédits obtenus/tentés"""
        return format_html(
            '<span style="color: {};">{}</span> / {}',
            'green' if obj.total_credits_earned == obj.total_credits_attempted else 'orange',
            obj.total_credits_earned,
            obj.total_credits_attempted
        )
    credits_display.short_description = 'Crédits (obtenus/tentés)'
    
    def gpa_breakdown(self, obj):
        """Affiche le détail des notes par cours"""
        enrollments = obj.student.enrollments.filter(
            course_section__semester=obj.semester,
            course_section__year=obj.year,
            status='COMPLETED'
        ).select_related('course_section__course', 'grade')
        
        if not enrollments.exists():
            return "Aucune inscription complétée"
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '''
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Cours</th>
                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Crédits</th>
                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Note</th>
                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Points GPA</th>
                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Statut</th>
            </tr>
        '''
        
        for enrollment in enrollments:
            try:
                grade = enrollment.grade
                if grade.final_grade is not None:
                    grade_value = float(grade.final_grade)
                    
                    # Calcul des points GPA
                    if grade_value >= 90:
                        points = 4.0
                        letter = 'A'
                    elif grade_value >= 80:
                        points = 3.0
                        letter = 'B'
                    elif grade_value >= 70:
                        points = 2.0
                        letter = 'C'
                    elif grade_value >= 60:
                        points = 1.0
                        letter = 'D'
                    else:
                        points = 0.0
                        letter = 'F'
                    
                    status = '✓ Réussi' if grade.is_passing() else '✗ Échoué'
                    status_color = 'green' if grade.is_passing() else 'red'
                    
                    html += f'''
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;">
                                {enrollment.course_section.course.code} - 
                                {enrollment.course_section.course.name}
                            </td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                                {enrollment.course_section.course.credits}
                            </td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                                <strong>{grade_value:.1f}</strong> ({letter})
                            </td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                                {points:.1f}
                            </td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd; color: {status_color};">
                                {status}
                            </td>
                        </tr>
                    '''
                else:
                    html += f'''
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;">
                                {enrollment.course_section.course.code} - 
                                {enrollment.course_section.course.name}
                            </td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                                {enrollment.course_section.course.credits}
                            </td>
                            <td colspan="3" style="padding: 8px; text-align: center; border: 1px solid #ddd; color: gray;">
                                Note non disponible
                            </td>
                        </tr>
                    '''
            except Exception:
                html += f'''
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">
                            {enrollment.course_section.course.code} - 
                            {enrollment.course_section.course.name}
                        </td>
                        <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                            {enrollment.course_section.course.credits}
                        </td>
                        <td colspan="3" style="padding: 8px; text-align: center; border: 1px solid #ddd; color: red;">
                            Erreur
                        </td>
                    </tr>
                '''
        
        html += '</table>'
        return format_html(html)
    gpa_breakdown.short_description = 'Détail des notes'
    
    @admin.action(description='Recalculer le GPA')
    def recalculate_gpa(self, request, queryset):
        """Recalcule le GPA pour les relevés sélectionnés"""
        count = 0
        for transcript in queryset:
            transcript.calculate_gpa()
            transcript.save()
            count += 1
        
        self.message_user(
            request,
            f"{count} relevé(s) de notes recalculé(s) avec succès."
        )
    
    def save_model(self, request, obj, form, change):
        """Calcule automatiquement le GPA lors de la sauvegarde"""
        obj.calculate_gpa()
        super().save_model(request, obj, form, change)