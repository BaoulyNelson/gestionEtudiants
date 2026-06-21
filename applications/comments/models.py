from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from applications.articles.models import Article


class Commentaire(models.Model):
    article    = models.ForeignKey(Article, on_delete=models.CASCADE,
                                   related_name='commentaire_set', verbose_name='Article')
    auteur     = models.ForeignKey(User,    on_delete=models.CASCADE,
                                   related_name='commentaires',    verbose_name='Auteur')
    contenu    = models.TextField(max_length=2000, verbose_name='Commentaire')
    parent     = models.ForeignKey('self', on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='replies',
                                   verbose_name='Reponse a')
    est_approuve = models.BooleanField(default=True, verbose_name='Approuve')
    cree_le  = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['cree_le']

    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur {self.article.titre[:30]}"
