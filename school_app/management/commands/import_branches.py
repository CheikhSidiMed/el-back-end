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
                FROM students
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
            # CONVERSION DES DATES
            # ----------------------------
            birth_date = parse_date(birth_date)
            tdate = parse_date(tdate)
            start = parse_date(start)
            date_desectivation = parse_date(date_desectivation)

            # ----------------------------
            # MAPPINGS LOGIQUES
            # ----------------------------
            etudiant_etat = 'inscrit' if is_active == 0 else 'suspendu'
            is_inscrire = 1 if etat == 0 else 0
            payment = 'mensuel' if etat == 'طبيعي' else 'free'
            etudiant_gender = 'M' if gender == 'أنثى' else 'F'
            date_inscription = date(2025, 12, 31)
            agent_id_n = agent_id if agent_id and agent_id != 0 else None

            etudiants.append(
                Etudiant(
                    id=id,
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
                    agent_id=agent_id_n,
                    phone=phone,
                    level_id=level_id,
                    rewaya=rewaya,
                    days=days,
                    tdate=tdate,
                    start=start,
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
# from school_app.models import Classe, Branche


# class Command(BaseCommand):
#     help = "Import classes from MySQL to PostgreSQL keeping same IDs"

#     def handle(self, *args, **options):
#         with connections['mysql_db'].cursor() as cursor:
#             cursor.execute("""
#                 SELECT class_id, branch_id, class_name
#                 FROM classes
#             """)
#             rows = cursor.fetchall()

#         classes_to_create = []

#         for row in rows:
#             class_id, branch_id, class_name = row

#             # Vérifier que la branche existe
#             try:
#                 branche = Branche.objects.get(id=branch_id)
#             except Branche.DoesNotExist:
#                 self.stdout.write(self.style.WARNING(
#                     f"Branche {branch_id} not found, skipping class {class_id}"
#                 ))
#                 continue

#             classes_to_create.append(
#                 Classe(
#                     id=class_id,     # ✅ conserve le même ID
#                     nom=class_name,
#                     branche_id=branch_id  # ou branche=branche
#                 )
#             )

#         with transaction.atomic():
#             Classe.objects.bulk_create(classes_to_create, ignore_conflicts=True)

#         self.stdout.write(
#             self.style.SUCCESS(f"{len(classes_to_create)} classes imported successfully")
#         )



# from django.core.management.base import BaseCommand
# from django.db import connections, transaction
# from school_app.models import Agent


# class Command(BaseCommand):
#     help = "Import agents from MySQL to PostgreSQL keeping same IDs"

#     def handle(self, *args, **options):
#         with connections['mysql_db'].cursor() as cursor:
#             cursor.execute("""
#                 SELECT agent_id, phone, agent_name, phone_2, profession, whatsapp_phone
#                 FROM agents
#             """)
#             rows = cursor.fetchall()

#         agents_to_create = []

#         for row in rows:
#             agent_id, phone, agent_name, phone_2, profession, whatsapp_phone = row

#             # Normalisation des champs optionnels
#             phone_2 = phone_2 or None
#             profession = profession or None
#             whatsapp_phone = whatsapp_phone or None

#             agents_to_create.append(
#                 Agent(
#                     id=agent_id,           # ✅ conserve le même ID
#                     agent_name=agent_name,
#                     phone=phone,
#                     phone_2=phone_2,
#                     profession=profession,
#                     whatsapp_phone=whatsapp_phone
#                 )
#             )

#         with transaction.atomic():
#             Agent.objects.bulk_create(agents_to_create, ignore_conflicts=True)

#         self.stdout.write(
#             self.style.SUCCESS(f"{len(agents_to_create)} agents imported successfully")
#         )










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
