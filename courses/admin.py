# ========== courses/admin.py - REMPLACER COMPLÈTEMENT ==========
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Course, CourseSection, Prerequisite
from django import forms


# ---- FORMULAIRE POUR L’ACTION ----
class CreateSectionForm(forms.Form):
    section_number = forms.CharField(label="Numéro de section", initial="A")
    day_of_week = forms.ChoiceField(
        choices=CourseSection.DAYS_CHOICES,
        label="Jour de la semaine"
    )
    start_time = forms.TimeField(label="Heure de début", initial="08:00")
    end_time = forms.TimeField(label="Heure de fin", initial="10:00")
    room = forms.CharField(label="Salle", required=False)
    session = forms.ChoiceField(choices=CourseSection.SESSION_CHOICES, label="Session")
    semester = forms.ChoiceField(choices=CourseSection.SEMESTER_CHOICES, label="Semestre")
    year = forms.IntegerField(label="Année académique", initial=2025)
    max_students = forms.IntegerField(label="Capacité", initial=30)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credits_badge', 'year_level_badge', 
                    'sections_count', 'is_active_display']
    list_filter = ['department', 'year_level', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'year_level']
    ordering = ['code']
    list_per_page = 20
    
    fieldsets = (
        ('📖 Informations principales', {
            'fields': ('code', 'name', 'description', 'credits')
        }),
        ('🏛️ Classification', {
            'fields': ('department', 'year_level')
        }),
        ('⚙️ Statut', {
            'fields': ('is_active',)
        }),
    )
    
    actions = ['activate_courses', 'deactivate_courses', 'duplicate_course', 'create_global_section']
    

    
    # --- BADGES D’AFFICHAGE ---

    def credits_badge(self, obj):
        return format_html(
            '<span style="background-color: #ffc107; color: black; padding: 3px 10px; border-radius: 3px;">{} crédits</span>',
            obj.credits
        )
    credits_badge.short_description = 'Crédits'
    
    def year_level_badge(self, obj):
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 3px 10px; border-radius: 3px;">Année {}</span>',
            obj.year_level
        )
    year_level_badge.short_description = 'Année'
    
    def sections_count(self, obj):
        count = obj.sections.count()
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">{} section(s)</span>',
            count
        )
    sections_count.short_description = 'Sections'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_active_display.short_description = 'Actif'
    
    # --- ACTIONS ---

    def activate_courses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} cours activé(s).')
    activate_courses.short_description = "✓ Activer les cours"
    
    def deactivate_courses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} cours désactivé(s).')
    deactivate_courses.short_description = "✗ Désactiver les cours"

    # --- FILTRAGE SPÉCIAL POUR NIVEAU 1 ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si l'URL contient year_level__exact=1 → on ne garde que les cours sans département
        if request.GET.get('year_level__exact') == '1':
            qs = qs.filter(department__isnull=True)
        return qs
    
    
    def create_global_section(self, request, queryset):
        created = 0
        for course in queryset:
            # Vérifie qu’il n’existe pas déjà une section “globale” pour ce cours
            if not CourseSection.objects.filter(course=course, section_number='G').exists():
                CourseSection.objects.create(
                    course=course,
                    section_number='G',  # ou "1" selon ta logique
                    professor=None,      # à remplir plus tard
                    day_of_week='Lundi',   # ou None selon ton modèle
                    start_time='07:00:00',
                    end_time='10:00:00',
                    session='2',         # exemple
                    semester='1',        # idem
                    year=2025,
                    max_students=30,
                    is_open=True,
                )
                created += 1

        self.message_user(request, f'{created} section(s) globale(s) créée(s).')
    create_global_section.short_description = "➕ Créer une section globale pour les cours sélectionnés"



@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ['section_display', 'course', 'professor_name', 'schedule_display', 
                    'session_badge', 'enrollment_status', 'is_open_display']
    
    # Ajout d'un filtre sur le niveau d'étude
    list_filter = [
        'session', 'semester', 'year', 'day_of_week', 'is_open', 'course__department',
        'course__year_level'  # <-- filtre par niveau d'étude
    ]
    
    search_fields = ['course__code', 'course__name', 'section_number', 'professor__user__last_name']
    raw_id_fields = ['course', 'professor']
    ordering = ['course__code', 'section_number']
    list_per_page = 20
    
    fieldsets = (
        ('📚 Cours', {'fields': ('course', 'section_number', 'professor')}),
        ('🕐 Horaire', {'fields': ('day_of_week', 'start_time', 'end_time', 'room')}),
        ('📅 Période académique', {'fields': ('session', 'semester', 'year')}),
        ('👥 Capacité et statut', {'fields': ('max_students', 'is_open')}),
    )
    
    actions = ['open_sections', 'close_sections', 'increase_capacity']
    
    def section_display(self, obj):
        return f"{obj.course.code}-{obj.section_number}"
    section_display.short_description = 'Section'

    
    def professor_name(self, obj):
        if obj.professor:
            return obj.professor.user.get_full_name()
        return format_html('<span style="color: red;">Non assigné</span>')
    professor_name.short_description = 'Professeur'
    
    def schedule_display(self, obj):
        return format_html(
            '<strong>{}</strong><br>{} - {}',
            obj.get_day_of_week_display(),
            obj.start_time.strftime('%H:%M'),
            obj.end_time.strftime('%H:%M')
        )
    schedule_display.short_description = 'Horaire'
    
    def session_badge(self, obj):
        return format_html(
            '<span style="background-color: #6610f2; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            obj.get_semester_display(),
            obj.year
        )
    session_badge.short_description = 'Période'
    
    def enrollment_status(self, obj):
        enrolled = obj.get_enrolled_count()
        max_students = obj.max_students
        percentage = (enrolled / max_students * 100) if max_students > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 70:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}/{}</span>',
            color, enrolled, max_students
        )
    enrollment_status.short_description = 'Inscriptions'
    
    def is_open_display(self, obj):
        if obj.is_open:
            return format_html('<span style="color: green; font-size: 18px;">🟢 Ouvert</span>')
        return format_html('<span style="color: red; font-size: 18px;">🔴 Fermé</span>')
    is_open_display.short_description = 'Statut'
    
    def open_sections(self, request, queryset):
        updated = queryset.update(is_open=True)
        self.message_user(request, f'{updated} section(s) ouverte(s).')
    open_sections.short_description = "🟢 Ouvrir aux inscriptions"
    
    def close_sections(self, request, queryset):
        updated = queryset.update(is_open=False)
        self.message_user(request, f'{updated} section(s) fermée(s).')
    close_sections.short_description = "🔴 Fermer aux inscriptions"
    
    def increase_capacity(self, request, queryset):
        for section in queryset:
            section.max_students += 5
            section.save()
        self.message_user(request, f'Capacité augmentée de 5 places pour {queryset.count()} section(s).')
    increase_capacity.short_description = "➕ Augmenter la capacité (+5)"


@admin.register(Prerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ['course', 'prerequisite_course']
    search_fields = ['course__code', 'prerequisite_course__code']
    raw_id_fields = ['course', 'prerequisite_course']