from django.core.management.base import BaseCommand
from django.db import connections
from decimal import Decimal
from school_app.models import Etudiant

class Command(BaseCommand):
    help = "Fix payment fields after import"

    def handle(self, *args, **options):
        with connections['mysql_db'].cursor() as cursor:
            cursor.execute("""
                SELECT id, payment_nature, fees, discount, remaining
                FROM students
            """)
            rows = cursor.fetchall()

        updated = 0

        for id, mysql_payment_nature, fees, discount, remaining in rows:
            if mysql_payment_nature == 'طبيعي':
                payment_nature = 'mensuel'
            else:
                payment_nature = 'free'
                fees = discount = remaining = 0

            updated += Etudiant.objects.filter(id=id).update(
                payment_nature=payment_nature,
                fees=Decimal(fees or 0),
                discount=Decimal(discount or 0),
                remaining=Decimal(remaining or 0),
            )

        self.stdout.write(self.style.SUCCESS(f"{updated} étudiants mis à jour"))
