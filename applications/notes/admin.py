from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from .models import Note, HistoriqueNote, Bulletin

@admin.register(Note)
class AdminNote(admin.ModelAdmin):
    list_display = [
        'info_etudiant', 'info_cours', 'composantes_note',
        'affichage_note_finale', 'badge_mention', 'note_par',
    ]
    list_filter = [
        'mention',
        'inscription__section_cours__cours__departement',  # Corrigé ici
        'modifie_le',
    ]
    search_fields = [
        'inscription__etudiant__numero_etudiant',  # Corrigé ici
        'inscription__etudiant__utilisateur__prenom',  # Corrigé ici
        'inscription__etudiant__utilisateur__nom',  # Corrigé ici
        'inscription__section_cours__cours__code',  # Corrigé ici
    ]
    raw_id_fields = ['inscription', 'note_par']
    ordering = ['-modifie_le']
    list_per_page = 20

    fieldsets = (
        ('📝 Inscription', {
            'fields': ('inscription',),
        }),
        ('📊 Composantes de la note', {
            'fields': ('examen_mi_parcours', 'examen_final', 'travaux', 'participation', 'projet'),
            'description': 'Pondérations : Mi-parcours 25 %, Final 35 %, Travaux 20 %, Participation 10 %, Projet 10 %',
        }),
        ('🎯 Résultat final', {
            'fields': ('note_finale', 'mention'),
        }),
        ('💬 Informations supplémentaires', {
            'fields': ('commentaires', 'note_par'),
        }),
    )

    readonly_fields = ['note_finale', 'mention']
    actions = ['recalculer_notes']

    # ------------------#
    # Colonnes personnalisées
    # ------------------#

    def info_etudiant(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.inscription.etudiant.numero_etudiant,  # Corrigé ici
            obj.inscription.etudiant.utilisateur.get_full_name(),  # Corrigé ici
        )
    info_etudiant.short_description = 'Étudiant'

    def info_cours(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>Section {}</small>',
            obj.inscription.section_cours.cours.code,  # Corrigé ici
            obj.inscription.section_cours.numero_section,  # Corrigé ici
        )
    info_cours.short_description = 'Cours'

    def composantes_note(self, obj):
        elements = []
        if obj.examen_mi_parcours: elements.append(f'📝 {obj.examen_mi_parcours}')
        if obj.examen_final:        elements.append(f'📄 {obj.examen_final}')
        if obj.travaux:             elements.append(f'📚 {obj.travaux}')
        if obj.participation:       elements.append(f'🗣️ {obj.participation}')
        if obj.projet:              elements.append(f'🎯 {obj.projet}')
        return format_html('<br>'.join(elements)) if elements else '-'
    composantes_note.short_description = 'Composantes'

    def affichage_note_finale(self, obj):
        if obj.note_finale:
            couleur = 'green' if float(obj.note_finale) >= 60 else 'red'
            return format_html(
                '<span style="color: {}; font-size: 18px; font-weight: bold;">{}</span>',
                couleur, obj.note_finale,
            )
        return '-'
    affichage_note_finale.short_description = 'Note finale'

    def badge_mention(self, obj):
        if obj.mention:
            couleurs = {
                'A': '#28a745', 'B': '#007bff',
                'C': '#17a2b8', 'D': '#ffc107', 'F': '#dc3545',
            }
            return format_html(
                '<span style="background-color: {}; color: white; padding: 5px 15px; '
                'border-radius: 3px; font-size: 16px; font-weight: bold;">{}</span>',
                couleurs.get(obj.mention, 'gray'),
                obj.mention,
            )
        return '-'
    badge_mention.short_description = 'Mention'

    # ------------------#
    # Actions
    # ------------------#

    @admin.action(description='🔄 Recalculer les notes sélectionnées')
    def recalculer_notes(self, request, queryset):
        for note in queryset:
            note.save()
        self.message_user(request, f'{queryset.count()} note(s) recalculée(s).')

@admin.register(HistoriqueNote)
class AdminHistoriqueNote(admin.ModelAdmin):
    list_display = ['note', 'composante', 'ancienne_valeur', 'nouvelle_valeur', 'modifie_par', 'modifie_le']
    list_filter = ['composante', 'modifie_le']
    search_fields = ['note__inscription__etudiant__numero_etudiant']  # Corrigé ici
    raw_id_fields = ['note', 'modifie_par']
    date_hierarchy = 'modifie_le'
    ordering = ['-modifie_le']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Bulletin)
class AdminBulletin(admin.ModelAdmin):
    list_display = ['etudiant', 'affichage_periode', 'affichage_gpa', 'affichage_credits', 'genere_le']

    list_filter = ['annee', 'semestre', 'genere_le']

    search_fields = [
        'etudiant__utilisateur__prenom',  # Corrigé ici
        'etudiant__utilisateur__nom',  # Corrigé ici
        'etudiant__numero_etudiant',  # Corrigé ici
    ]

    readonly_fields = ['genere_le', 'gpa', 'credits_tentes', 'credits_obtenus', 'detail_notes']
    fieldsets = (
        ('Informations de base', {
            'fields': ('etudiant', 'semestre', 'annee'),
        }),
        ('Statistiques', {
            'fields': ('gpa', 'credits_tentes', 'credits_obtenus', 'detail_notes'),
        }),
        ('Métadonnées', {
            'fields': ('genere_le',),
            'classes': ('collapse',),
        }),
    )

    actions = ['recalculer_gpa']

    # ------------------#
    # Colonnes personnalisées
    # ------------------#

    def affichage_periode(self, obj):
        """Affiche la période sous la forme 'Semestre Année'"""
        return f"{obj.semestre} {obj.annee}"
    affichage_periode.short_description = 'Période'
    affichage_periode.admin_order_field = 'annee'

    def affichage_gpa(self, obj):
        """Affiche le GPA avec un code couleur"""
        if obj.gpa is None:
            return format_html('<span style="color: gray;">N/A</span>')

        if obj.gpa >= 3.5:
            couleur = 'green'
        elif obj.gpa >= 3.0:
            couleur = 'blue'
        elif obj.gpa >= 2.0:
            couleur = 'orange'
        else:
            couleur = 'red'

        return format_html('<strong style="color: {};">{:.2f}</strong>', couleur, obj.gpa)
    affichage_gpa.short_description = 'GPA'
    affichage_gpa.admin_order_field = 'gpa'

    def affichage_credits(self, obj):
        """Affiche les crédits obtenus sur les crédits tentés"""
        couleur = 'green' if obj.credits_obtenus == obj.credits_tentes else 'orange'
        return format_html(
            '<span style="color: {};">{}</span> / {}',
            couleur, obj.credits_obtenus, obj.credits_tentes,
        )
    affichage_credits.short_description = 'Crédits (obtenus / tentés)'

    def detail_notes(self, obj):
        """Tableau récapitulatif des notes par cours pour ce semestre"""
        inscriptions = obj.etudiant.inscriptions.filter(  # Corrigé ici
            section_cours__semestre=obj.semestre,  # Corrigé ici
            section_cours__annee=obj.annee,  # Corrigé ici
            statut='COMPLETE',  # Corrigé ici
        ).select_related('section_cours__cours', 'note')  # Corrigé ici

        if not inscriptions.exists():
            return "Aucune inscription complétée pour cette période."

        lignes = []
        for inscription in inscriptions:
            try:
                note = inscription.note
                if note.note_finale is not None:
                    valeur = float(note.note_finale)
                    if valeur >= 90:
                        points, lettre = 4.0, 'A'
                    elif valeur >= 80:
                        points, lettre = 3.0, 'B'
                    elif valeur >= 70:
                        points, lettre = 2.0, 'C'
                    elif valeur >= 60:
                        points, lettre = 1.0, 'D'
                    else:
                        points, lettre = 0.0, 'F'

                    statut = '✓ Réussi' if note.est_recu() else '✗ Échoué'
                    couleur_statut = 'green' if note.est_recu() else 'red'
                    lignes.append(f"""
                        <tr>
                            <td style="padding:8px;border:1px solid #ddd;">
                                {inscription.section_cours.cours.code} –
                                {inscription.section_cours.cours.nom}
                            </td>
                            <td style="padding:8px;text-align:center;border:1px solid #ddd;">
                                {inscription.section_cours.cours.credits}
                            </td>
                            <td style="padding:8px;text-align:center;border:1px solid #ddd;">
                                <strong>{valeur:.1f}</strong> ({lettre})
                            </td>
                            <td style="padding:8px;text-align:center;border:1px solid #ddd;">
                                {points:.1f}
                            </td>
                            <td style="padding:8px;text-align:center;border:1px solid #ddd;color:{couleur_statut};">
                                {statut}
                            </td>
                        </tr>
                    """)
                else:
                    lignes.append(f"""
                        <tr>
                            <td style="padding:8px;border:1px solid #ddd;">
                                {inscription.section_cours.cours.code} –
                                {inscription.section_cours.cours.nom}
                            </td>
                            <td style="padding:8px;text-align:center;border:1px solid #ddd;">
                                {inscription.section_cours.cours.credits}
                            </td>
                            <td colspan="3" style="padding:8px;text-align:center;border:1px solid #ddd;color:gray;">
                                Note non disponible
                            </td>
                        </tr>
                    """)
            except Exception:
                lignes.append(f"""
                    <tr>
                        <td style="padding:8px;border:1px solid #ddd;">
                            {inscription.section_cours.cours.code} –
                            {inscription.section_cours.cours.nom}
                        </td>
                        <td colspan="4" style="padding:8px;text-align:center;border:1px solid #ddd;color:red;">
                            Erreur lors de la récupération de la note
                        </td>
                    </tr>
                """)

        entete = """
            <tr style="background-color:#f0f0f0;">
                <th style="padding:8px;text-align:left;border:1px solid #ddd;">Cours</th>
                <th style="padding:8px;text-align:center;border:1px solid #ddd;">Crédits</th>
                <th style="padding:8px;text-align:center;border:1px solid #ddd;">Note</th>
                <th style="padding:8px;text-align:center;border:1px solid #ddd;">Points GPA</th>
                <th style="padding:8px;text-align:center;border:1px solid #ddd;">Statut</th>
            </tr>
        """
        tableau = (
            '<table style="width:100%;border-collapse:collapse;">'
            + entete + ''.join(lignes) + '</table>'
        )
        return format_html(tableau)
    detail_notes.short_description = 'Détail des notes'

    # ------------------#
    # Actions
    # ------------------#

    @admin.action(description='Recalculer le GPA des relevés sélectionnés')
    def recalculer_gpa(self, request, queryset):
        nombre = 0
        for bulletin in queryset:
            bulletin.calculer_gpa()
            bulletin.save()
            nombre += 1
        self.message_user(request, f"{nombre} relevé(s) recalculé(s) avec succès.")

    def save_model(self, request, obj, form, change):
        """Recalcule le GPA automatiquement à chaque sauvegarde admin"""
        obj.calculer_gpa()
        super().save_model(request, obj, form, change)