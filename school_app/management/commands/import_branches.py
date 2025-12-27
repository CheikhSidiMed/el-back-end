from django.core.management.base import BaseCommand
from django.db import connections, transaction
from datetime import date

from school_app.models import Etudiant


class Command(BaseCommand):
    help = "Import students from MySQL to PostgreSQL with same ID and mapping rules"

    def handle(self, *args, **options):
        with connections['mysql_db'].cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    student_name,
                    part_count,
                    gender,
                    birth_date,
                    birth_place,
                    registration_date,
                    regstration_date_count,
                    student_photo,
                    payment_nature,
                    fees,
                    discount,
                    remaining,
                    class_id,
                    branch_id,
                    agent_id,
                    phone,
                    level_id,
                    rewaya,
                    days,
                    tdate,
                    start,
                    is_active,
                    elmoutoune,
                    balance,
                    date_desectivation,
                    suspension_reason,
                    current_city,
                    etat
                FROM students LIMIT 1
            """)
            rows = cursor.fetchall()

        etudiants = []

        for row in rows:
            (
                id,
                student_name,
                part_count,
                gender,
                birth_date,
                birth_place,
                registration_date,
                reg_date_count,
                student_photo,
                payment_nature,
                fees,
                discount,
                remaining,
                class_id,
                branch_id,
                agent_id,
                phone,
                level_id,
                rewaya,
                days,
                tdate,
                start,
                is_active,
                elmoutoune,
                balance,
                date_desectivation,
                suspension_reason,
                current_city,
                etat,
            ) = row

            # ----------------------------
            # MAPPINGS LOGIQUES
            # ----------------------------

            # is_active (0 → inscrit, else suspendu)
            etudiant_etat = 'inscrit' if is_active == 0 else 'suspendu'

            # students.etat (0 → is_inscrire = 1, else 0)
            is_inscrire = 1 if etat == 0 else 0

            # payment_nature
            payment = 'mensuel' if etat == 'طبيعي' else 'free'

            # gender
            etudiant_gender = 'M' if gender == 'أنثى' else 'F'

            # date_inscription
            date_inscription = date(2025, 12, 31)

            etudiants.append(
                Etudiant(
                    id=id,  # ✅ CONSERVE LE MÊME ID
                    student_name=student_name,
                    part_count=part_count or 1,
                    is_inscrire=is_inscrire,
                    gender=etudiant_gender,
                    birth_date=birth_date,
                    birth_place=birth_place,
                    date_inscription=date_inscription,
                    date_count=reg_date_count,
                    student_photo=student_photo,
                    payment_nature=payment,
                    fees=fees or 0,
                    discount=discount or 0,
                    remaining=remaining or 0,
                    classe_id=class_id,
                    branche_id=branch_id,
                    agent_id=agent_id,
                    phone=phone,
                    level_id=level_id,
                    rewaya=rewaya,
                    days=days,
                    tdate=tdate,
                    start=start,
                    is_active=is_active,
                    elmoutoune=elmoutoune,
                    balance=balance or 0,
                    date_desectivation=date_desectivation,
                    suspension_reason=suspension_reason,
                    current_city=current_city,
                    etat=etudiant_etat,
                )
            )

        with transaction.atomic():
            Etudiant.objects.bulk_create(etudiants, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f"{len(etudiants)} étudiants importés avec succès")
        )

















# from django.core.management.base import BaseCommand
# from django.db import connections, transaction
# from school_app.models import Branche

# class Command(BaseCommand):
#     help = "Import branches from MySQL to PostgreSQL"

#     def handle(self, *args, **options):
#         with connections['mysql_db'].cursor() as cursor:
#             cursor.execute("""
#                 SELECT nom, adresse
#                 FROM branches
#             """)
#             rows = cursor.fetchall()

#         branches = [
#             Branche(nom=nom, adresse=adresse)
#             for nom, adresse in rows
#         ]

#         with transaction.atomic():
#             Branche.objects.bulk_create(branches)

#         self.stdout.write(self.style.SUCCESS("Branches imported successfully"))
