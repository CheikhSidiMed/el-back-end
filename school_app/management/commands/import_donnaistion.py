from django.core.management.base import BaseCommand
from django.db import connections, transaction
from datetime import date, datetime
from school_app.models import Transaction


def parse_date(d):
    """Convertit une date MySQL en objet date Django, None si vide ou invalide"""
    if not d or d == '':
        return None
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    try:
        # Si c’est une chaîne, on suppose format YYYY-MM-DD
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None


class Command(BaseCommand):
    help = "Import students from MySQL to PostgreSQL with same ID and mapping rules"

    def handle(self, *args, **options):
        with connections['mysql_db'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    transaction_description, 
                    amount, 
                    transaction_type, 
                    bank_id, 
                    transaction_date
                FROM donate_transactions WHERE id = 10005
            """)
            rows = cursor.fetchall()

        transactions = []

        for row in rows:
            (
                transaction_description, 
                amount, 
                transaction_type, 
                bank_id, 
                transaction_date
            ) = row

            # ----------------------------
            # CONVERSION DES DATES
            # ----------------------------
            date = parse_date(transaction_date)

            transactions.append(
                Transaction(
                    account=18,
                    paid_amount=amount,
                    date=date,
                    description=transaction_description,
                    type=transaction_type,
                    bank = (
                        3 if bank_id == 4 else
                        5 if bank_id == 20 else
                        6 if bank_id == 2 else
                        7 if bank_id == 3 else
                        8 if bank_id == 19 else
                        9 if bank_id == 5 else
                        2 if bank_id is None else
                        bank_id
                    ),
                    user=bank_id,

                )
            )

        with transaction.atomic():
            Transaction.objects.bulk_create(transactions, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f"{len(transactions)} transactions importés avec succès")
        )
