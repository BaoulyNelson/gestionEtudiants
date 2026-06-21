from django.contrib import admin
from .models import Commentaire


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display  = ('auteur', 'article', 'est_approuve', 'cree_le', 'apercu')
    list_filter   = ('est_approuve', 'cree_le')
    search_fields = ('auteur__username', 'contenu', 'article__titre')
    list_editable = ('est_approuve',)
    date_hierarchy = 'cree_le'
    actions = ['approuver', 'masquer']

    def apercu(self, obj):
        return obj.contenu[:80]
    apercu.short_description = 'Contenu'

    def approuver(self, request, queryset):
        queryset.update(est_approuve=True)
        self.message_user(request, f'{queryset.count()} commentaire(s) approuve(s).')
    approuver.short_description = 'Approuver la selection'

    def masquer(self, request, queryset):
        queryset.update(est_approuve=False)
        self.message_user(request, f'{queryset.count()} commentaire(s) masque(s).')
    masquer.short_description = 'Masquer la selection'
