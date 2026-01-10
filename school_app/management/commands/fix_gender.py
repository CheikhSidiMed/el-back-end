from django.core.management.base import BaseCommand
from django.db import connections
from school_app.models import Etudiant

class Command(BaseCommand):
    help = "Fix gender field after import"

    def handle(self, *args, **options):
        with connections['mysql_db'].cursor() as cursor:
            cursor.execute("""
                SELECT id, gender
                FROM students
            """)
            rows = cursor.fetchall()

        updated = 0

        for student_id, gender in rows:
            # règle demandée
            etudiant_gender = 'M' if gender == 'ذكر' else 'F'

            updated += Etudiant.objects.filter(id=student_id).update(
                gender=etudiant_gender
            )

        self.stdout.write(
            self.style.SUCCESS(f"{updated} étudiants mis à jour (gender uniquement)")
        )
