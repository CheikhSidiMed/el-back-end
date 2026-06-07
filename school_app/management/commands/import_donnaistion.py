from django.core.management.base import BaseCommand
from django.db import connections, transaction
from datetime import date, datetime
from school_app.models import Etudiant


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
                    donate_account_id, 
                    transaction_description, 
                    amount, 
                    transaction_type, 
                    bank_id, 
                    transaction_date
                FROM donate_transactions
            """)
            rows = cursor.fetchall()

        transactions = []

        for row in rows:
            (
                donate_account_id, 
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
                    account=donate_account_id,
                    paid_amount=amount,
                    date=date,
                    description=transaction_description,
                    type=transaction_type,
                    bank=bank_id or 0,
                    user=bank_id,

                )
            )

        with transaction.atomic():
            Transaction.objects.bulk_create(transactions, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f"{len(transactions)} transactions importés avec succès")
        )

[
    {
        "id": 1,
        "bank_name": "بنكيلي",
        "account_number": "5501",
        "balance": "89633.88",
        "category": 2,
        "user": null
    },
    {
        "id": 2,
        "bank_name": "صندوق فرع البنات و الوقف",
        "account_number": "5602",
        "balance": "715186.00",
        "category": 1,
        "user": null
    },
    {
        "id": 3,
        "bank_name": "بيم بنك",
        "account_number": "5504",
        "balance": "31000.00",
        "category": 2,
        "user": null
    },
    {
        "id": 4,
        "bank_name": "الصندوق - المركزي",
        "account_number": "5601",
        "balance": "90038.27",
        "category": 1,
        "user": null
    },
    {
        "id": 5,
        "bank_name": "غزة بي",
        "account_number": "5506",
        "balance": "49169.35",
        "category": 2,
        "user": null
    },
    {
        "id": 6,
        "bank_name": "السداد",
        "account_number": "5503",
        "balance": "217081.32",
        "category": 2,
        "user": null
    },
    {
        "id": 7,
        "bank_name": "مصرفي",
        "account_number": "5502",
        "balance": "190664.52",
        "category": 2,
        "user": null
    },
    {
        "id": 8,
        "bank_name": "كليك",
        "account_number": "5505",
        "balance": "30900.00",
        "category": 2,
        "user": null
    },
    {
        "id": 9,
        "bank_name": "أخرى",
        "account_number": "5506",
        "balance": "36694.00",
        "category": 1,
        "user": null
    }
]
