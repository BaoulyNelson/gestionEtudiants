"""
Commande d'import des départements de base.

Emplacement attendu : departements/management/commands/import_departements.py
(adapter l'app si la tienne porte un autre nom).

Usage :
    python manage.py import_departements
"""

from django.core.management.base import BaseCommand

from applications.departements.models import Departement


class Command(BaseCommand):
    help = "Crée ou met à jour les départements de base (PSY, COMM, SOCIO, TS)."

    # Ces valeurs sont des valeurs par défaut raisonnables.
    # Tu pourras toujours les ajuster ensuite via l'admin Django
    # (description, image_hero_url, conditions_admission, etc.)
    DEPARTEMENTS = [
        {
            "code": "PSY",
            "slug": "psychologie",
            "nom": "Psychologie",
            "couleur": "primary",
            "emoji": "🧠",
            "slogan": "Comprendre l'esprit humain",
            "ordre": 1,
        },
        {
            "code": "COMM",
            "slug": "communication",
            "nom": "Communication Sociale",
            "couleur": "secondary",
            "emoji": "📣",
            "slogan": "Informer, connecter, influencer",
            "ordre": 2,
        },
        {
            "code": "SOCIO",
            "slug": "sociologie",
            "nom": "Sociologie",
            "couleur": "success",
            "emoji": "🌍",
            "slogan": "Décrypter la société",
            "ordre": 3,
        },
        {
            "code": "TS",
            "slug": "travail-social",
            "nom": "Travail Social",
            "couleur": "accent",
            "emoji": "🤝",
            "slogan": "Accompagner et soutenir",
            "ordre": 4,
        },
    ]

    def handle(self, *args, **options):
        crees = 0
        maj = 0

        for data in self.DEPARTEMENTS:
            departement, created = Departement.objects.update_or_create(
                code=data["code"],
                defaults={
                    "slug": data["slug"],
                    "nom": data["nom"],
                    "couleur": data["couleur"],
                    "emoji": data["emoji"],
                    "slogan": data["slogan"],
                    "ordre": data["ordre"],
                },
            )
            if created:
                crees += 1
                self.stdout.write(self.style.SUCCESS(f"Créé : {departement}"))
            else:
                maj += 1
                self.stdout.write(f"Mis à jour : {departement}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTerminé. {crees} département(s) créé(s), {maj} mis à jour."
            )
        )