from django.core.management.base import BaseCommand
from django.db import connections, transaction
from school_app.models import Branche

class Command(BaseCommand):
    help = "Import branches from MySQL to PostgreSQL"

    def handle(self, *args, **options):
        with connections['mysql_db'].cursor() as cursor:
            cursor.execute("""
                SELECT nom, adresse
                FROM branches
            """)
            rows = cursor.fetchall()

        branches = [
            Branche(nom=nom, adresse=adresse)
            for nom, adresse in rows
        ]

        with transaction.atomic():
            Branche.objects.bulk_create(branches)

        self.stdout.write(self.style.SUCCESS("Branches imported successfully"))
