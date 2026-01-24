from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Branche, Classe, Niveau, Agent, Receipt, SalaryPayment, ReceiptPayment, Exam, AbsElmhdara, Job, Inscription, Garant, GarantPaiement, Employee, Transaction, Etudiant, Mois, Paiement, BankAccount, Receipt, ReceiptPayment, Utilisateur, Activity, AcademicYear, MonthlyReport, DailyAbsence, AccountCategory, Account, Permission, Suspension, AbsenceActivity
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action

from django.db.models import Sum, Count
from calendar import monthrange
from collections import defaultdict
from rest_framework.views import APIView
from dateutil.relativedelta import relativedelta

from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from django.utils import timezone
from datetime import date, datetime

from calendar import monthrange
from decimal import Decimal
from rest_framework import status

from django.dispatch import receiver

from django.db.models.signals import post_save, pre_save, post_delete
from .pagination import EtudiantPagination
from rest_framework import filters
from django.db import transaction as db_transaction
from .filters import UtilisateurFilter
from rest_framework.permissions import AllowAny


MONTHS_AR = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}

ARABIC_MONTHS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]

class BrancheViewSet(viewsets.ModelViewSet):
    serializer_class = BrancheSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # admin général → كل الفروع
        if user.role and user.role.title == 'admin_g':
            return Branche.objects.all()

        # 🟢 ManyToMany: user.branches
        if hasattr(user, 'branches'):
            return user.branches.all()

        # 🟡 ForeignKey: user.branche
        if hasattr(user, 'branche') and user.branche:
            return Branche.objects.filter(id=user.branche.id)

        # 🔴 لا يملك أي فرع
        return Branche.objects.none()

    # def get_queryset(self):
        user = self.request.user

        # Superuser → toutes les branches
        if user.is_superuser:
            return Branche.objects.all()

        return user.branches.all()

class ClasseViewSet(viewsets.ModelViewSet):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['branche']

class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['branche']

class AbsElmhdaraViewSet(viewsets.ModelViewSet):
    queryset = AbsElmhdara.objects.all()
    serializer_class = AbsElmhdaraSerializer
    filter_backends = [DjangoFilterBackend]
    
class NiveauViewSet(viewsets.ModelViewSet):
    queryset = Niveau.objects.all()
    serializer_class = NiveauSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

class AbsenceActivityViewSet(viewsets.ModelViewSet):
    queryset = AbsenceActivity.objects.all()
    serializer_class = AbsenceActivitySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activity']

class EtudiantViewSet(viewsets.ModelViewSet):
    queryset = Etudiant.objects.all()
    serializer_class = EtudiantSerializer
    pagination_class = EtudiantPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['student_name', 'id', 'phone', 'agent__agent_name', 'agent__phone', 'agent__phone_2', 'agent__whatsapp_phone', 'classe__nom', 'branche__nom' ]
    filterset_fields = ['agent_id', 'payment_nature', 'branche_id', 'classe_id', 'etat', 'classe'] 

    def get_queryset(self):
        queryset = Etudiant.objects.all()
        inscrire_param = self.request.query_params.get('inscrire', None)

        if inscrire_param is None or inscrire_param == '1':
            queryset = queryset.filter(is_inscrire=1)
        elif inscrire_param == '0':
            queryset = queryset.filter(is_inscrire=0)


        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Validation Error:", serializer.errors)
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

class MoisViewSet(viewsets.ModelViewSet):
    queryset = Mois.objects.all()
    serializer_class = MoisSerializer

class AccountCategoryViewSet(viewsets.ModelViewSet):
    queryset = AccountCategory.objects.all()
    serializer_class = AccountCategorySerializer

class InscriptionViewSet(viewsets.ModelViewSet):
    queryset = Inscription.objects.all()
    serializer_class = InscriptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activity', 'student']

class GarantViewSet(viewsets.ModelViewSet):
    queryset = Garant.objects.all()
    serializer_class = GarantSerializer
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['activity', 'student']

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)

        # إنشاء إيصال مرتبط بالعملية
        receipt = Receipt.objects.create(
            student=transaction.student,
            agent=transaction.agent,
            account=transaction.account,
            employee=transaction.employee,
            total_amount=transaction.paid_amount,
            receipt_date=timezone.now().date(),
            created_by=self.request.user,
            receipt_description=transaction.description
        )

        ReceiptPayment.objects.create(
            receipt=receipt,
            transaction=transaction
        )
        return transaction, receipt

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction, receipt = self.perform_create(serializer)

        return Response({
            "message": "Paiement traité avec succès",
            "receipt_id": receipt.pk,
            # "receipt_date": receipt.receipt_date.strftime("%Y-%m-%d | %H:%M"),
            "receipt_date": transaction.date.strftime("%Y-%m-%d | %H:%M"),
            "created_by": transaction.user.first_name if transaction.user else None,
            "transaction": serializer.data
        }, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        with db_transaction.atomic():

            old_instance = self.get_object()
            old_amount = old_instance.paid_amount

            # 🔹 update sans toucher au solde
            updated_tx = serializer.save(is_adjustment=True)

            delta = updated_tx.paid_amount - old_amount

            if delta != 0:
                # 🔹 appliquer uniquement la différence
                if delta > 0:
                    updated_tx.bank.balance += delta
                    tx_type = "plus"
                else:
                    updated_tx.bank.balance -= abs(delta)
                    tx_type = "minus"

                updated_tx.bank.save()

                # 🔹 historique (optionnel)
                Transaction.objects.create(
                    student=updated_tx.student,
                    bank=updated_tx.bank,
                    account=updated_tx.account,
                    employee=updated_tx.employee,
                    inscription=updated_tx.inscription,
                    user=self.request.user,
                    paid_amount=abs(delta),
                    type=tx_type,
                    description=f"تعديل على المعاملة رقم {updated_tx.id} / {updated_tx.description}",
                    is_adjustment=True,
                    related_transaction=updated_tx,
                )

            return updated_tx

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)

        transaction = self.perform_update(serializer)

        return Response(
            {
                "message": "تم تعديل المعاملة بنجاح ",
                "transaction": TransactionSerializer(transaction).data,
            },
            status=status.HTTP_200_OK,
        )

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated] 
    filterset_fields = ['agent', 'etudiant']

    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        """
        Process payment: use single-student logic if no agent, multi-student logic if agent exists.
        """
        data = request.data
        agent_id = data.get("agent")
        payments = data.get("payments", [])  # list of {student, month, due_amount, paid_amount}
        extras = data.get("extras", [])  # list of {student, month, due_amount, paid_amount}
        bank_id = data.get("bank")
        agent_name = data.get("agent_name")


        if not payments and not extras:
            return Response({"error": "No payments provided"}, status=400)

        with transaction.atomic():

            # if not agent_id:
            #     created_transactions = []

            #     # --- Paiement sans agent (pour un seul étudiant) ---
            #     student_id = data.get("student")
            #     if not student_id:
            #         return Response({"error": "No student provided for payment"}, status=400)
            #     student = Etudiant.objects.get(id=student_id)

            #     # 🔹 Combine all items (months + extras)
            #     total_amount = (
            #         sum(p["paid_amount"] for p in payments)
            #         + sum(e["amount"] for e in extras)
            #     )

            #     # 🔹 Build description
            #     month_part = (
            #         f" الأشهر: {', '.join(p['month_name_ar'] for p in payments)}"
            #         if payments else ""
            #     )
            #     extra_part = (
            #         " + " + ", ".join(e["des"] for e in extras)
            #         if extras else ""
            #     )
            #     description = f"الطالب(ة) {payments[0]['student_name'] if payments else student.student_name}  سدد(ت) {month_part} {extra_part}"

            #     # Create Receipt
            #     receipt = Receipt.objects.create(
            #         student=student,
            #         agent_id=None,
            #         total_amount=total_amount,
            #         receipt_date=timezone.now(),
            #         created_by=request.user,
            #         receipt_description=description
            #     )

            #     # Create Transaction (global one for both months + extras)
            #     if payments:
            #         txn = Transaction.objects.create(
            #             student=student,
            #             agent_id=None,
            #             month=', '.join(str(p["month"]) for p in payments) if payments else None,
            #             due_amount=sum(p["due_amount"] for p in payments) if payments else 0,
            #             paid_amount=total_amount,
            #             remaining_amount=sum(p["remaining_amount"] for p in payments) if payments else 0,
            #             date=timezone.now(),
            #             description = f"الطالب(ة) {payments[0]['student_name']} سدد(ت) الأشهر: {{ {', '.join(p['month_name_ar'] for p in payments)} }}",
            #             bank_id=bank_id,
            #             user=request.user
            #         )
            #         ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
            #         created_transactions.append(txn.id)

            #     if extras:
            #         for ex in extras:
            #             txn = Transaction.objects.create(
            #                 student=student,
            #                 agent_id=None,
            #                 month=None,
            #                 due_amount=0,
            #                 paid_amount=ex["amount"],
            #                 remaining_amount=0,
            #                 date=timezone.now(),
            #                 description = f"الطالب(ة) {ex['student_name']} سدد(ت) : {{ {ex['des']} }}",
            #                 bank_id=bank_id,
            #                 user=request.user
            #             )
            #             ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
            #             created_transactions.append(txn.id)

            #     # 🔹 Créer ou mettre à jour les enregistrements de paiement pour chaque mois
            #     for p in payments:
            #         paiement, created = Paiement.objects.get_or_create(
            #             etudiant=student,
            #             academic_year_id=p.get("academic_year"),
            #             month=p["month"],
            #             defaults={
            #                 "due_amount": p["due_amount"],
            #                 "paid_amount": p["paid_amount"],
            #                 "remaining_amount": max(0, p["due_amount"] - p["paid_amount"]),
            #                 "bank_id": bank_id,
            #                 "agent_id": None,
            #                 "user": request.user
            #             }
            #         )

            #         if not created:
            #             # 🔄 Mise à jour du paiement existant
            #             paiement.paid_amount += p["paid_amount"]
            #             paiement.remaining_amount = max(0, p["due_amount"] - paiement.paid_amount)
            #             paiement.due_amount = p["due_amount"]  # au cas où le montant dû change
            #             paiement.bank_id = bank_id
            #             paiement.user = request.user
            #             paiement.save()

            if not agent_id:
                created_transactions = []

                student_id = data.get("student")
                if not student_id:
                    return Response({"error": "No student provided"}, status=400)

                student = Etudiant.objects.get(pk=student_id)

                # 🔹 Totaux
                total_due = sum(Decimal(str(p["due_amount"])) for p in payments)
                total_paid_months = sum(Decimal(str(p["paid_amount"])) for p in payments)
                total_extras = sum(Decimal(str(e["amount"])) for e in extras)
                total_paid = total_paid_months + total_extras
                total_remaining = max(Decimal("0.0"), total_due - total_paid_months)

                months_str = ", ".join(str(p["month"]) for p in payments)
                months_ar = ", ".join(p["month_name_ar"] for p in payments)

                description = f"الطالب(ة) {student.student_name} سدد(ت) الأشهر: {{ {months_ar} }}"
                if extras:
                    description += " + " + ", ".join(e["des"] for e in extras)

                # 🧾 Receipt
                receipt = Receipt.objects.create(
                    student=student,
                    agent_id=None,
                    total_amount=total_paid,
                    receipt_date=timezone.now(),
                    created_by=request.user,
                    receipt_description=description
                )

                # 💳 Transaction principale (mois)
                if payments:
                    txn = Transaction.objects.create(
                        student=student,
                        agent_id=None,
                        month=months_str,
                        due_amount=total_due,
                        paid_amount=total_paid_months,
                        remaining_amount=total_remaining,
                        date=timezone.now(),
                        description=description,
                        bank_id=bank_id,
                        user=request.user
                    )
                    ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
                    created_transactions.append(txn.pk)

                # ➕ Extras (transactions séparées)
                for ex in extras:
                    txn = Transaction.objects.create(
                        student=student,
                        agent_id=None,
                        month=None,
                        due_amount=0,
                        paid_amount=Decimal(str(ex["amount"])),
                        remaining_amount=0,
                        date=timezone.now(),
                        description=f"الطالب(ة) {student.student_name} سدد(ت): {{ {ex['des']} }}",
                        bank_id=bank_id,
                        user=request.user
                    )
                    ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
                    created_transactions.append(txn.pk)

                # 📊 Paiement (cumulatif par mois)
                for p in payments:
                    paiement, created = Paiement.objects.get_or_create(
                        etudiant=student,
                        academic_year_id=p["academic_year"],
                        month=p["month"],
                        defaults={
                            "due_amount": Decimal(str(p["due_amount"])),
                            "paid_amount": Decimal(str(p["paid_amount"])),
                            "remaining_amount": max(
                                Decimal("0.0"),
                                Decimal(str(p["due_amount"])) - Decimal(str(p["paid_amount"]))
                            ),
                            "bank_id": bank_id,
                            "agent_id": None,
                            "user": request.user
                        }
                    )

                    if not created:
                        paiement.paid_amount += Decimal(str(p["paid_amount"]))
                        paiement.remaining_amount = max(
                            Decimal("0.0"),
                            paiement.due_amount - paiement.paid_amount
                        )
                        paiement.bank_id = bank_id
                        paiement.user = request.user
                        paiement.save()

            # else:
            #     # --- Paiement avec agent (plusieurs étudiants) ---
            #     total_paid = (
            #         sum(p["paid_amount"] for p in payments)
            #         + sum(e["amount"] for e in extras)
            #     )

            #     # 🔹 Build description
            #     month_part = (
            #         f" الأشهر: {', '.join(p['month_name_ar'] for p in payments)}"
            #         if payments else ""
            #     )
            #     extra_part = (
            #         " + " + ", ".join(e["des"] for e in extras)
            #         if extras else ""
            #     )
            #     description = f"الوكيل(ة) {agent_name}  دفع(ت) {month_part} {extra_part} "

            #     receipt = Receipt.objects.create(
            #         student=None,
            #         agent_id=agent_id,
            #         total_amount=total_paid,
            #         receipt_date=timezone.now(),
            #         created_by=request.user,
            #         receipt_description=description
            #     )

            #     created_transactions = []
            #     if payments:
            #         txn = Transaction.objects.create(
            #             student=None,
            #             agent_id=agent_id,
            #             month=', '.join(str(p["month"]) for p in payments) if payments else None,
            #             due_amount=sum(p["due_amount"] for p in payments) if payments else 0,
            #             paid_amount=total_paid,
            #             remaining_amount=sum(p["remaining_amount"] for p in payments) if payments else 0,
            #             date=timezone.now(),
            #             description = f"الوكيل(ة) {agent_name} سدد(ت) الأشهر: {{ {', '.join(p['month_name_ar'] for p in payments)} }}",
            #             bank_id=bank_id,
            #             user=request.user
            #         )
            #         ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
            #         created_transactions.append(txn.id)

            #     if extras:
            #         for ex in extras:
            #             txn = Transaction.objects.create(
            #                 student=None,
            #                 agent_id=agent_id,
            #                 month=None,
            #                 due_amount=0,
            #                 paid_amount=ex["amount"],
            #                 remaining_amount=0,
            #                 date=timezone.now(),
            #                 description = f"الوكيل(ة) {agent_name} سدد(ت) : {{ {ex['des']} }}",
            #                 bank_id=bank_id,
            #                 user=request.user
            #             )
            #             ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
            #             created_transactions.append(txn.id)


            #     for p in payments:
            #         student = Etudiant.objects.get(id=p["student"])

            #         paiement, created = Paiement.objects.get_or_create(
            #             etudiant=student,
            #             academic_year_id=p.get("academic_year"),
            #             month=p["month"],
            #             defaults={
            #                 "due_amount": Decimal(str(p["due_amount"])),
            #                 "paid_amount": Decimal(str(p["paid_amount"])),
            #                 "remaining_amount": max(
            #                     Decimal('0.0'),
            #                     Decimal(str(p["due_amount"])) - Decimal(str(p["paid_amount"]))
            #                 ),
            #                 "bank_id": bank_id,
            #                 "agent_id": agent_id,
            #                 "user": request.user
            #             }
            #         )

            #         if not created:
            #             # 🔄 Paiement existe déjà → mise à jour du montant
            #             paiement.paid_amount += Decimal(str(p["paid_amount"]))
            #             paiement.due_amount = Decimal(str(p["due_amount"]))
            #             paiement.remaining_amount = max(
            #                 Decimal('0.0'),
            #                 paiement.due_amount - paiement.paid_amount
            #             )
            #             paiement.bank_id = bank_id
            #             paiement.agent_id = agent_id
            #             paiement.user = request.user
            #             paiement.save()


            #         created_transactions.append(txn.id)

            else:
                # ================================
                # 🔹 Paiement avec agent
                # ================================

                created_transactions = []

                # 🔹 Totaux
                total_due = sum(Decimal(str(p["due_amount"])) for p in payments)
                total_paid_months = sum(Decimal(str(p["paid_amount"])) for p in payments)
                total_extras = sum(Decimal(str(e["amount"])) for e in extras)
                total_paid = total_paid_months + total_extras
                total_remaining = max(Decimal("0.0"), total_due - total_paid_months)

                # 🔹 Mois combinés
                months_str = ", ".join(str(p["month"]) for p in payments)
                months_ar = ", ".join(p["month_name_ar"] for p in payments)

                # 🔹 Description
                description = f"الوكيل(ة) {agent_name} سدد(ت) الأشهر: {{ {months_ar} }}"
                if extras:
                    description += " + " + ", ".join(e["des"] for e in extras)

                # ================================
                # 🧾 Receipt
                # ================================
                receipt = Receipt.objects.create(
                    student=None,
                    agent_id=agent_id,
                    total_amount=total_paid,
                    receipt_date=timezone.now(),
                    created_by=request.user,
                    receipt_description=description
                )

                # ================================
                # 💳 Transaction principale (mois groupés)
                # ================================
                if payments:
                    txn = Transaction.objects.create(
                        student=None,
                        agent_id=agent_id,
                        month=months_str,
                        due_amount=total_due,
                        paid_amount=total_paid_months,
                        remaining_amount=total_remaining,
                        date=timezone.now(),
                        description=description,
                        bank_id=bank_id,
                        user=request.user
                    )
                    ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
                    created_transactions.append(txn.pk)

                # ================================
                # ➕ Transactions extras
                # ================================
                for ex in extras:
                    txn = Transaction.objects.create(
                        student=None,
                        agent_id=agent_id,
                        month=None,
                        due_amount=0,
                        paid_amount=Decimal(str(ex["amount"])),
                        remaining_amount=0,
                        date=timezone.now(),
                        description=f"الوكيل(ة) {agent_name} سدد(ت): {{ {ex['des']} }}",
                        bank_id=bank_id,
                        user=request.user
                    )
                    ReceiptPayment.objects.create(receipt=receipt, transaction=txn)
                    created_transactions.append(txn.pk)

                # ================================
                # 📊 Paiement (cumulatif par étudiant / mois)
                # ================================
                for p in payments:
                    student = Etudiant.objects.get(pk=p["student"])

                    paiement, created = Paiement.objects.get_or_create(
                        etudiant=student,
                        academic_year_id=p["academic_year"],
                        month=p["month"],
                        defaults={
                            "due_amount": Decimal(str(p["due_amount"])),
                            "paid_amount": Decimal(str(p["paid_amount"])),
                            "remaining_amount": max(
                                Decimal("0.0"),
                                Decimal(str(p["due_amount"])) - Decimal(str(p["paid_amount"]))
                            ),
                            "bank_id": bank_id,
                            "agent_id": agent_id,
                            "user": request.user
                        }
                    )

                    if not created:
                        paiement.paid_amount += Decimal(str(p["paid_amount"]))
                        paiement.remaining_amount = max(
                            Decimal("0.0"),
                            paiement.due_amount - paiement.paid_amount
                        )
                        paiement.bank_id = bank_id
                        paiement.agent_id = agent_id
                        paiement.user = request.user
                        paiement.save()



        return Response({
            "message": "Paiement traité avec succès",
            "receipt_id": receipt.pk,
            "receipt_date": receipt.receipt_date.strftime("%Y-%m-%d | %H:%M:%S"),
            "transactions": created_transactions,
            "created_by": request.user.first_name,
        })

    def perform_update(self, serializer):
        with db_transaction.atomic():

            paiement = self.get_object()

            old_paid = paiement.paid_amount
            new_paid = Decimal(self.request.data.get("paid_amount"))
            new_bank = self.request.data.get("bank_id")
            delta = new_paid - old_paid
            remaining_amount =  paiement.due_amount - new_paid



            # 1️⃣ Update paiement
            paiement.paid_amount = new_paid
            paiement.bank_id = new_bank
            paiement.remaining_amount = remaining_amount
            paiement.save()

            # ⛔ No change → no transaction
            if delta == 0:
                return

            etudiant = paiement.etudiant
            student_name = etudiant.student_name if etudiant else ""
            # # 2️⃣ Update bank balance
            # bank.balance += delta
            # bank.save()

            month_number = paiement.month
            month_name = MONTHS_AR.get(month_number, "")

            # 3️⃣ Create adjustment transaction
            Transaction.objects.create(
                student=paiement.etudiant,
                agent=paiement.agent,
                month=str(paiement.month),
                due_amount=paiement.due_amount,
                paid_amount=abs(delta),
                remaining_amount=remaining_amount,
                description=f"تعديل دفع شهر {month_name}, {student_name}",
                type="plus" if delta > 0 else "minus",
                bank_id=new_bank,
                user=self.request.user,
                is_adjustment=False,
                related_transaction=None  # or original transaction if you store it
            )

    @action(detail=True, methods=['post'])
    def delete_payment(self, request, pk=None):
        """
        Supprime un paiement et ajuste le solde de la banque + enregistre la transaction d'annulation.
        """
        try:
            paiement = self.get_object()
            bank = paiement.bank

            with transaction.atomic():
                paid_amount = Decimal(str(paiement.paid_amount))
                student = paiement.etudiant

                # 🔹 Supprimer le paiement
                paiement.delete()

                # 🔹 Mettre à jour le solde de la banque (si le modèle contient 'balance')
                if bank and hasattr(bank, "balance"):
                    bank.balance = Decimal(bank.balance) - Decimal(paid_amount)
                    bank.save()
                # 🔹 Créer une description lisible en arabe
                month_name_ar = paiement.month_name if hasattr(paiement, "get_month_display") else ARABIC_MONTHS[int(paiement.month) - 1]
                description = f"تم حذف دفعة الطالب(ة) {student.student_name} لشهر {month_name_ar} بمبلغ {paid_amount}."

                # 🔹 Créer un reçu d'annulation
                receipt = Receipt.objects.create(
                    student=student,
                    agent_id=None,
                    total_amount=-paid_amount,  # montant négatif pour indiquer une suppression
                    receipt_date=timezone.now(),
                    created_by=request.user,
                    receipt_description=description
                )

                # 🔹 Créer une transaction d'annulation
                txn = Transaction.objects.create(
                    student=student,
                    agent_id=None,
                    type='minus',
                    month=paiement.month,
                    due_amount=0,
                    paid_amount=paid_amount,
                    remaining_amount=0,
                    date=timezone.now(),
                    description=description,
                    bank_id=bank.id if bank else None,
                    user=request.user
                )

                ReceiptPayment.objects.create(receipt=receipt, transaction=txn)

            return Response({
                "message": " Paiement supprimé avec succès.",
                "bank": bank.id if bank else None,
                "new_balance": str(bank.balance) if bank and hasattr(bank, "balance") else None
            }, status=status.HTTP_200_OK)

        except Paiement.DoesNotExist:
            return Response({"error": "Paiement introuvable."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Erreur : {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class GarantPaiementViewSet(viewsets.ModelViewSet):
    queryset = GarantPaiement.objects.all()
    serializer_class = GarantPaiementSerializer
    permission_classes = [IsAuthenticated] 

    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        data = request.data
        payments = data.get("payments")
        bank_id = data.get("bank")
        garant_id = data.get("garant")
        account_id = data.get("account")

        if not payments or not garant_id:
            return Response({"error": "Missing data"}, status=400)

        with transaction.atomic():
            garant = Garant.objects.get(id=garant_id)

            # -------------------------------
            # 🔹 COMBINAISON DES DONNÉES
            # -------------------------------
            months = []
            total_due = 0
            total_paid = 0

            for p in payments:
                months.append(p["month"])
                total_due += p["due_amount"]
                total_paid += p["paid_amount"]

            remaining_amount = max(0, total_due - total_paid)
            months_names = [MONTHS_AR.get(m, str(m)) for m in months]

            # -------------------------------
            # 🔹 RECEIPT
            # -------------------------------
            receipt = Receipt.objects.create(
                garant=garant,
                agent_id=None,
                account_id=account_id,
                total_amount=total_paid,
                receipt_date=timezone.now(),
                created_by=request.user,
                receipt_description=f"الكافل(ة) {garant.name} سدد(ت) الأشهر: {{ {', '.join(months_names)} }}"

            )

            # -------------------------------
            # 🔹 UNE SEULE TRANSACTION
            # -------------------------------
            txn = Transaction.objects.create(
                garant=garant,
                agent_id=None,
                # month=", ".join(months),
                account_id=account_id,
                description=f"الكافل(ة) {garant.name} سدد(ت) الأشهر: {{ {', '.join(months_names)} }}",
                due_amount=total_due,
                paid_amount=total_paid,
                remaining_amount=remaining_amount,
                date=timezone.now(),
                bank_id=bank_id,
                user=request.user
            )

            ReceiptPayment.objects.create(
                receipt=receipt,
                transaction=txn
            )

            # -------------------------------
            # 🔹 GARANT PAIEMENT (par mois)
            # -------------------------------
            for p in payments:
                gp, _ = GarantPaiement.objects.get_or_create(
                    garant=garant,
                    academic_year_id=p.get("academic_year"),
                    month=p["month"],
                    defaults={
                        "due_amount": p["due_amount"],
                        "paid_amount": 0,
                        "remaining_amount": p["due_amount"],
                        "bank_id": bank_id,
                        "user": request.user,
                    }
                )

                gp.paid_amount += p["paid_amount"]
                gp.remaining_amount = max(0, gp.due_amount - gp.paid_amount)
                gp.bank_id = bank_id
                gp.user = request.user
                gp.save()

        return Response({
            "message": "Paiement traité avec succès",
            "receipt_id": receipt.pk,
            "receipt_date": receipt.receipt_date.strftime("%Y-%m-%d | %H:%M:%S"),
            "transactions": txn.description,
            "created_by": request.user.first_name,
        })

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer

class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

class RolePermissionsView(APIView):
    def get(self, request, role_code):
        try:
            job = Job.objects.get(title=role_code)
        except Job.DoesNotExist:
            return Response({"error": "Role not found"}, status=404)

        serializer = JobSerializer(job)
        return Response(serializer.data)

class PermissionTreeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roots = Permission.objects.filter(parent__isnull=True)
        serializer = PermissionTreeSerializer(roots, many=True)
        return Response(serializer.data)

class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer

class ReceiptPaymentViewSet(viewsets.ModelViewSet):
    queryset = ReceiptPayment.objects.all()
    serializer_class = ReceiptPaymentSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    # queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    def get_queryset(self):
        return (
            Activity.objects
            .annotate(
                students_count=Count("inscription")
            )
        )

class DailyAbsenceViewSet(viewsets.ModelViewSet):
    queryset = DailyAbsence.objects.all()
    serializer_class = DailyAbsenceSerializer

class SuspensionViewSet(viewsets.ModelViewSet):
    queryset = Suspension.objects.all()
    serializer_class = SuspensionSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filterset_fields = ['is_actif']

    @action(detail=True, methods=['post'], url_path='activate')
    def activate_employee(self, request, pk=None):
        """
        POST /api/employees/{id}/activate/
        {
            "subscription_date": "2025-11-03"
        }
        ➤ Réactive un employé et met à jour la date d'abonnement (تاريخ العودة للعمل)
        """
        try:
            employee = self.get_object()
        except Employee.DoesNotExist:
            return Response({"success": False, "message": "الموظف غير موجود."}, status=404)

        if employee.is_actif:
            return Response({"success": False, "message": "الموظف نشط بالفعل."}, status=400)

        # 🔹 Lire la date saisie
        date_str = request.data.get("subscription_date")
        if not date_str:
            return Response(
                {"success": False, "message": "يرجى إدخال تاريخ العودة إلى العمل."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"success": False, "message": "تاريخ غير صالح."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Mise à jour
        employee.is_actif = True
        employee.subscription_date = new_date
        employee.save(update_fields=["is_actif", "subscription_date"])

        return Response(
            {
                "success": True,
                "message": f"تم إعادة تفعيل {employee.full_name} بتاريخ {new_date}."
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss_employee(self, request, pk=None):
        """
        POST /api/employees/{id}/dismiss/
        {
        "date": "2025-11-02",
        "confirm": true|false
        }

        ➤ Si confirm=False → calcule المستحقات فقط (prévisualisation)
        ➤ Si confirm=True  → désactive l’employé et enregistre le montant dans balance
        """
        try:
            employee = self.get_object()
        except Employee.DoesNotExist:
            return Response({"success": False, "message": "الموظف غير موجود."}, status=404)

        # 🔹 Lire la date
        date_str = request.data.get("date")
        if not date_str:
            return Response({"success": False, "message": "يرجى إدخال تاريخ الفصل."}, status=400)

        try:
            dismiss_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"success": False, "message": "تاريخ غير صالح."}, status=400)

        # 🔹 Trouver l’année académique correspondante
        current_year = (
            AcademicYear.objects
            .order_by("-start_date")
            .first()
        )
        if not current_year:
            return Response({"success": False, "message": "لا توجد سنة مالية حالية."}, status=400)

        month = dismiss_date.month

        # 🔹 Vérifier si le salaire du mois est déjà payé
        month_paid = SalaryPayment.objects.filter(
            employee=employee, academic_year=current_year, month=month
        ).exists()

        current_month_salary = Decimal("0.00")
        if not month_paid:
            days_in_month = 30
            worked_days = dismiss_date.day
            prorata = Decimal(worked_days) / Decimal(days_in_month)
            current_month_salary = (employee.salary or Decimal("0.00")) * prorata

        total_due = (employee.balance or Decimal("0.00")) + current_month_salary

        # 🔹 Mode prévisualisation ou confirmation
        confirm = str(request.data.get("confirm", "false")).lower() == "true"

        if confirm:
            # ✅ On enregistre le solde et on désactive
            with transaction.atomic():
                employee.balance = total_due
                employee.is_actif = False
                employee.save(update_fields=["balance", "is_actif"])

            return Response({
                "success": True,
                "message": f"تم فصل الموظف {employee.full_name} بتاريخ {dismiss_date}.",
                "data": {
                    "employee": employee.full_name,
                    "new_balance": float(total_due),
                    "dismiss_date": dismiss_date.strftime("%Y-%m-%d"),
                    "month": month,
                    "academic_year": current_year.year
                }
            }, status=200)

        # 🟡 Sinon, simple prévisualisation
        return Response({
            "success": True,
            "preview": True,
            "data": {
                "employee": employee.full_name,
                "balance": float(employee.balance or 0),
                "current_month_salary": float(current_month_salary),
                "total_due": float(total_due),
                "month": month,
                "academic_year": current_year.year,
                "dismiss_date": dismiss_date.strftime("%Y-%m-%d"),
            }
        }, status=200)

class SalaryPaymentViewSet(viewsets.ModelViewSet):
    queryset = SalaryPayment.objects.all()
    serializer_class = SalaryPaymentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        if year:
            qs = qs.filter(academic_year__year=year)
        if month:
            qs = qs.filter(month=month)
        return qs

    @action(detail=False, methods=['post'], url_path='process')
    def process_month(self, request):
        """
        POST /api/salary-payments/process/
        {
          "year": "2025-2026",
          "month": 3,
          "employees": [
              {"id": 1, "amount": 500000},
              {"id": 2, "amount": 450000}
          ]
        }
        ➤ Crée des salaires pour les employés sélectionnés uniquement.
        """
        year_name = request.data.get("year")
        month = request.data.get("month")
        employees_data = request.data.get("employees", [])

        if not year_name or not month:
            return Response(
                {"success": False, "message": "يجب تحديد السنة والشهر."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            academic_year = AcademicYear.objects.get(year=year_name)
        except AcademicYear.DoesNotExist:
            return Response(
                {"success": False, "message": "السنة الأكاديمية غير موجودة."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not employees_data:
            return Response(
                {"success": False, "message": "لم يتم تحديد أي موظف."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, skipped = 0, 0

        with transaction.atomic():
            for e in employees_data:
                emp_id = e.get("id")
                amount = Decimal(str(e.get("amount", 0)))

                try:
                    emp = Employee.objects.get(id=emp_id, is_actif=True)
                except Employee.DoesNotExist:
                    skipped += 1
                    continue

                try:
                    obj, created_flag = SalaryPayment.objects.get_or_create(
                        employee=emp,
                        academic_year=academic_year,
                        month=month,
                        defaults={
                            "amount": amount,
                            "note": f"Paiement manuel mois {month}",
                        },
                    )
                    if created_flag:
                        created += 1
                    else:
                        skipped += 1
                except IntegrityError:
                    skipped += 1

        msg = f"تمت معالجة الرواتب لشهر {month} للسنة {year_name}."
        if skipped:
            msg += f" تم تخطي {skipped} موظف (مسجل مسبقاً أو غير صالح)."

        return Response({"success": True, "message": msg})
       
class MonthlyReportViewSet(viewsets.ModelViewSet):
    queryset = MonthlyReport.objects.all()
    serializer_class = MonthlyReportSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')

        if student_id and month and year:
            queryset = queryset.filter(
                student_id=student_id,
                month=month,
                year=year
            )
        return queryset

class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UtilisateurFilter

    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        user = self.get_object()

        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        # 🔒 تحقق من وجود البيانات
        if not current_password or not new_password:
            return Response(
                {"detail": "البيانات غير مكتملة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔑 تحقق من كلمة المرور الحالية
        if not user.check_password(current_password):
            return Response(
                {"detail": "كلمة المرور الحالية غير صحيحة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔁 تحديث كلمة المرور
        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "تم تحديث كلمة المرور بنجاح"},
            status=status.HTTP_200_OK
        )
            
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class AcademicYearViewSet(viewsets.ModelViewSet):
    """Full CRUD for AcademicYear (list, retrieve, create, update, delete)."""
    queryset         = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    lookup_field     = "id"

class RegisterUserView(generics.CreateAPIView):
    serializer_class = UtilisateurRegisterSerializer
    permission_classes = [AllowAny]

class BankTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BankTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source = BankAccount.objects.get(id=serializer.validated_data["source_bank_id"])
        destination = BankAccount.objects.get(id=serializer.validated_data["destination_bank_id"])
        amount = serializer.validated_data["amount"]
        desc_extra = serializer.validated_data.get("description", "")

        description = (
            f"نقل الأموال من حساب {source.bank_name} ({source.account_number}) "
            f"إلى حساب {destination.bank_name} ({destination.account_number})"
        )
        if desc_extra:
            description += f" {{ {desc_extra} }}"

        with db_transaction.atomic():

            # 🔻 Transaction débit (source)
            Transaction.objects.create(
                bank=source,
                paid_amount=amount,
                type="minus",
                description=description,
                user=request.user,
            )

            # 🔺 Transaction crédit (destination)
            Transaction.objects.create(
                bank=destination,
                paid_amount=amount,
                type="plus",
                description=description,
                user=request.user,
            )

        return Response({
            "message": "تم تحويل الأموال بنجاح",
            "amount": amount,
            "from": source.id,
            "to": destination.id
        })

class ClasseEffectifAPIView(APIView):
    def get(self, request, classe_id):
        try:
            classe = Classe.objects.get(id=classe_id)
        except Classe.DoesNotExist:
            return Response(
                {"error": "Classe introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        nombre_inscrits = classe.etudiants.filter(
            etat='inscrit'
        ).count()

        return Response({
            "classe_id": classe.id,
            "classe": classe.nom,
            "niveau": classe.niveau,
            "totals": nombre_inscrits
        })


@api_view(['GET'])
def daily_absence_list(request):
    queryset = DailyAbsence.objects.all()
    month = request.query_params.get('month')  # ex: '07'
    year = request.query_params.get('year')    # ex: '2024-2025'

    if month and year:
        try:
            month_int = int(month.lstrip('0'))  # '07' => 7
            queryset = queryset.filter(
                date__month=month_int,
                currentYear__iexact=year.strip()  # ignore espaces
            )
        except ValueError:
            return Response({"error": "Invalid month format"}, status=400)

    serializer = DailyAbsenceSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def student_payments(request):
    student_id = request.GET.get('student_id')
    year_id = request.GET.get('academic_year')
    full_month_fee = request.GET.get('month_fee')

    # Vérifier le montant mensuel
    try:
        full_month_fee = Decimal(full_month_fee)
    except:
        return Response({"error": "Invalid month_fee"}, status=400)

    # Récupérer l'étudiant et l'année académique
    try:
        student = Etudiant.objects.get(id=student_id)
        academic_year = AcademicYear.objects.get(id=year_id)
    except:
        return Response({"error": "Invalid student or academic year"}, status=400)

    # Paiements existants
    payments = Paiement.objects.filter(
        etudiant=student,
        academic_year=academic_year
    ).values('month', 'paid_amount', 'remaining_amount')
    payments_dict = {p['month']: p for p in payments}

    registration_date = student.date_inscription
    registration_year = registration_date.year
    year_selected = int(academic_year.name)  # <-- Utilisation de name

    result = []

    for month in range(1, 13):
        payment = payments_dict.get(month)

        # ---------------------------
        # Année sélectionnée avant inscription
        # ---------------------------
        if year_selected < registration_year:
            if payment:
                remaining_amount = Decimal(payment['remaining_amount'])
                due_amount = Decimal(payment['paid_amount']) + remaining_amount
                paid_amount = Decimal(payment['paid_amount'])
                status, status_bool = ("unpaid", False) if remaining_amount > 0 else ("paid", True)
            else:
                # Pas de paiement → considérer payé car étudiant pas encore inscrit
                due_amount = paid_amount = remaining_amount = Decimal("0.00")
                status, status_bool = "paid", True

        # ---------------------------
        # Année sélectionnée = année d'inscription
        # ---------------------------
        elif year_selected == registration_year:
            if month < registration_date.month:
                due_amount = paid_amount = remaining_amount = Decimal("0.00")
                status, status_bool = "paid", True
            elif month == registration_date.month:
                days_in_month = monthrange(registration_year, month)[1]
                proportion = Decimal(days_in_month - registration_date.day + 1) / Decimal(days_in_month)
                due_amount = (full_month_fee * proportion).quantize(Decimal("0.01"))

                if payment:
                    paid_amount = Decimal(payment['paid_amount'])
                    remaining_amount = due_amount - paid_amount
                else:
                    paid_amount = Decimal("0.00")
                    remaining_amount = due_amount

                if remaining_amount <= 0:
                    status, status_bool = "paid", True
                elif paid_amount > 0:
                    status, status_bool = "partial", False
                else:
                    status, status_bool = "unpaid", False
            else:
                due_amount = full_month_fee
                if payment:
                    paid_amount = Decimal(payment['paid_amount'])
                    remaining_amount = Decimal(payment['remaining_amount']) if payment.get('remaining_amount') is not None else due_amount - paid_amount
                else:
                    paid_amount = Decimal("0.00")
                    remaining_amount = due_amount

                if remaining_amount <= 0:
                    status, status_bool = "paid", True
                elif paid_amount > 0:
                    status, status_bool = "partial", False
                else:
                    status, status_bool = "unpaid", False

        # ---------------------------
        # Année sélectionnée après inscription
        # ---------------------------
        else:
            due_amount = full_month_fee
            if payment:
                paid_amount = Decimal(payment['paid_amount'])
                remaining_amount = Decimal(payment['remaining_amount']) if payment.get('remaining_amount') is not None else due_amount - paid_amount
            else:
                paid_amount = Decimal("0.00")
                remaining_amount = due_amount

            if remaining_amount <= 0:
                status, status_bool = "paid", True
            elif paid_amount > 0:
                status, status_bool = "partial", False
            else:
                status, status_bool = "unpaid", False

        result.append({
            "month": month,
            "month_name_ar": ARABIC_MONTHS[month - 1],
            "status": status,
            "status_bool": status_bool,
            "due_amount": float(due_amount),
            "paid_amount": float(paid_amount),
            "remaining_amount": float(remaining_amount)
        })

    return Response(result)


@api_view(['GET'])
def unpaid_months_until_suspend(request):
    student_id = request.GET.get('student_id')
    suspend_date = request.GET.get('suspend_date')
    full_month_fee = request.GET.get('month_fee')

    try:
        suspend_date = date.fromisoformat(suspend_date)
        full_month_fee = Decimal(full_month_fee)
    except:
        return Response({"error": "Invalid suspend_date or month_fee"}, status=400)

    try:
        student = Etudiant.objects.get(id=student_id)
    except:
        return Response({"error": "Student not found"}, status=404)

    if suspend_date <= student.date_inscription:
        return Response({"error": "Suspend before inscription"}, status=400)

    arabic_months = [
        'يناير','فبراير','مارس','أبريل','مايو','يونيو',
        'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'
    ]

    unpaid = []

    # 🔑 toutes les années scolaires concernées
    academic_years = AcademicYear.objects.filter(
        start_date__lte=suspend_date
    ).order_by('start_date')

    for academic_year in academic_years:

        payments = Paiement.objects.filter(
            etudiant=student,
            academic_year=academic_year
        ).values('month', 'paid_amount')

        payments_dict = {
            p['month']: Decimal(p['paid_amount']) for p in payments
        }

        academic_year_start = academic_year.start_date.year
        academic_year_end = academic_year.end_date.year

        same_year = academic_year_start <= student.date_inscription.year <= academic_year_end
        registration_month = student.date_inscription.month
        registration_day = student.date_inscription.day

        for month in range(1, 13):

            month_start = date(academic_year_start, month, 1)
            
            # ❌ mois après suspension
            if month_start >= suspend_date.replace(day=1) and academic_year_start == suspend_date.year and month > suspend_date.month:
                continue

            # ============================
            # AVANT inscription
            # ============================
            if same_year and month < registration_month:
                due_amount = Decimal("0.00")

            # ============================
            # Cas spécial : inscription ET suspension le même mois
            # ============================
            elif (
                same_year
                and month == registration_month
                and month == suspend_date.month
            ):
                days = monthrange(academic_year_start, month)[1]

                days_present = suspend_date.day - registration_day  # ⚠️ jour suspension exclu

                # sécurité
                if days_present < 0:
                    days_present = 0

                proportion = Decimal(days_present) / Decimal(days)
                due_amount = (full_month_fee * proportion).quantize(Decimal("0.01"))

            # ============================
            # MOIS inscription
            # ============================
            elif same_year and month == registration_month:
                days = monthrange(academic_year_start, month)[1]
                proportion = Decimal(days - registration_day + 1) / Decimal(days)
                due_amount = (full_month_fee * proportion).quantize(Decimal("0.01"))


            # ============================
            # MOIS suspension (⚠️ jour exclu)
            # ============================

            elif (
                (academic_year.start_date.year == suspend_date.year
                or academic_year.end_date.year == suspend_date.year)
                and month == suspend_date.month
            ):
                paid_amount = payments_dict.get(month, Decimal("0.00"))

                days = monthrange(academic_year_start, month)[1]
                days_present = suspend_date.day - 1  # ⚠️ jour exclu
                proportion = Decimal(days_present) / Decimal(days)
                due_amount = (full_month_fee * proportion).quantize(Decimal("0.01"))

            # ============================
            # MOIS normal
            # ============================
            else:
                due_amount = full_month_fee

            paid_amount = payments_dict.get(month, Decimal("0.00"))
            remaining = due_amount - paid_amount

            if remaining > 0:
                unpaid.append({
                    "academic_year": academic_year.year,
                    "month": month,
                    "month_name_ar": arabic_months[month - 1],
                    "due_amount": float(due_amount),
                    "paid_amount": float(paid_amount),
                    "remaining_amount": float(remaining)
                })

    return Response({
        "student_id": student.id,
        "suspend_date": suspend_date,
        "total_unpaid": float(sum(u["remaining_amount"] for u in unpaid)),
        "unpaid_months": unpaid
    })


@api_view(['GET'])
def garant_payments(request):
    garant_id = request.GET.get('garant_id')
    year_id = request.GET.get('academic_year')
    full_month_fee = request.GET.get('month_fee')

    # Convert month_fee to Decimal
    try:
        full_month_fee = Decimal(full_month_fee) if full_month_fee else Decimal("0")
    except:
        return Response({"error": "Invalid month_fee value"}, status=400)

    # Arabic month names
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]

    # Validate garant + year
    try:
        garant = Garant.objects.get(id=garant_id)
        academic_year = AcademicYear.objects.get(id=year_id)
    except (Etudiant.DoesNotExist, AcademicYear.DoesNotExist):
        return Response({"error": "Invalid garant or academic year"}, status=400)


    # Get all recorded payments
    payments = GarantPaiement.objects.filter(
        garant=garant,
        academic_year=academic_year
    ).values('month', 'due_amount', 'paid_amount', 'remaining_amount')

    payments_dict = {p['month']: p for p in payments}

    result = []
    for month in range(1, 12 + 1):

        # Normal month
        due_amount = full_month_fee
        payment = payments_dict.get(month)
        if payment:
            paid_amount = payment['paid_amount']
            remaining_amount = due_amount - paid_amount

            if remaining_amount <= 0:
                status, status_bool = "paid", True
            elif paid_amount > 0:
                status, status_bool = "partial", False
            else:
                status, status_bool = "unpaid", False
        else:
            paid_amount = Decimal("0.00")
            remaining_amount = due_amount
            status, status_bool = "unpaid", False

        result.append({
            "month": month,
            "month_name_ar": arabic_months[month - 1],
            "status": status,
            "status_bool": status_bool,
            "due_amount": float(due_amount),       # convert to float for JSON
            "paid_amount": float(paid_amount),
            "remaining_amount": float(remaining_amount)
        })

    return Response(result)


# On sauvegarde l'ancien état avant la mise à jour
@receiver(pre_save, sender=Transaction)
def store_old_values(sender, instance, **kwargs):

    if instance.pk:
        try:
            old_instance = Transaction.objects.get(pk=instance.pk)
            instance._old_paid_amount = old_instance.paid_amount
            instance._old_type = old_instance.type
            instance._old_bank = old_instance.bank
            instance._old_account = old_instance.account
            instance._old_employee = old_instance.employee
            instance._old_inscription = old_instance.inscription
        except Transaction.DoesNotExist:
            instance._old_paid_amount = 0
            instance._old_type = None
    else:
        instance._old_paid_amount = 0
        instance._old_type = None


@receiver(post_save, sender=Transaction)
def update_balances_on_save(sender, instance, created, **kwargs):

    # Ignorer les transactions d’ajustement
    if instance.is_adjustment:
        return

    def update_balance(obj, field_name, amount, operation):

        if not obj:
            return
        amount = Decimal(str(amount))
        current_balance = getattr(obj, field_name, Decimal('0.0'))
        if operation == "plus":
            setattr(obj, field_name, current_balance + amount)
        elif operation == "minus":
            setattr(obj, field_name, current_balance - amount)
        obj.save()

    # Si c’est une nouvelle transaction
    if created:
        update_balance(instance.bank, "balance", instance.paid_amount, instance.type)
        update_balance(instance.account, "balance", instance.paid_amount, instance.type)
        update_balance(instance.employee, "balance", instance.paid_amount, instance.type)
        update_balance(instance.inscription, "montant_pay", instance.paid_amount, instance.type)

    # Si c’est une mise à jour
    else:
        old_amount = getattr(instance, "_old_paid_amount", 0)
        old_type = getattr(instance, "_old_type", None)

        # On annule l'ancien effet
        if old_type:
            reverse_op = "minus" if old_type == "plus" else "plus"
            update_balance(instance._old_bank, "balance", old_amount, reverse_op)
            update_balance(instance._old_account, "balance", old_amount, reverse_op)
            update_balance(instance._old_employee, "balance", old_amount, reverse_op)
            update_balance(instance._old_inscription, "montant_pay", old_amount, reverse_op)

        # Puis on applique la nouvelle version
        update_balance(instance.bank, "balance", instance.paid_amount, instance.type)
        update_balance(instance.account, "balance", instance.paid_amount, instance.type)
        update_balance(instance.employee, "balance", instance.paid_amount, instance.type)
        update_balance(instance.inscription, "montant_pay", instance.paid_amount, instance.type)


# Optionnel : si tu veux restaurer les soldes quand une transaction est supprimée
@receiver(post_delete, sender=Transaction)
def restore_balances_on_delete(sender, instance, **kwargs):
    def update_balance(obj, field_name, amount, operation):
        if not obj:
            return
        current_balance = getattr(obj, field_name, 0)
        if operation == "plus":
            setattr(obj, field_name, current_balance - amount)
        elif operation == "minus":
            setattr(obj, field_name, current_balance + amount)
        obj.save()

    update_balance(instance.bank, "balance", instance.paid_amount, instance.type)
    update_balance(instance.account, "balance", instance.paid_amount, instance.type)
    update_balance(instance.employee, "balance", instance.paid_amount, instance.type)
    update_balance(instance.inscription, "montant_pay", instance.paid_amount, instance.type)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_transactions(request):
    today = date.today()

    # 🔹 Dates par défaut = aujourd’hui
    start_date = request.GET.get("start_date", today)
    end_date = request.GET.get("end_date", today)

    # 🔹 Utilisateur par défaut = user connecté
    user_id = request.GET.get("user_id", request.user.id)

    # ---- Transactions dans l'intervalle ----
    transactions = Transaction.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date,
        user_id=user_id
    ).order_by("date")

    serializer = TransactionSerializer(transactions, many=True)

    # ---- Totaux période ----
    total_plus_bank = transactions.filter(type="plus").exclude(bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    total_minus_bank = transactions.filter(type="minus").exclude(bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    total_plus_fund = transactions.filter(type="plus", bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    total_minus_fund = transactions.filter(type="minus", bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    # ---- Solde avant start_date ----
    before_tx = Transaction.objects.filter(
        date__date__lt=start_date,
        user_id=user_id
    )

    before_plus_bank = before_tx.filter(type="plus").exclude(bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    before_minus_bank = before_tx.filter(type="minus").exclude(bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    before_plus_fund = before_tx.filter(type="plus", bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    before_minus_fund = before_tx.filter(type="minus", bank__category=1)\
        .aggregate(s=Sum("paid_amount"))["s"] or 0

    return Response({
        "filters": {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "user_id": user_id
        },
        "transactions": serializer.data,
        "totals": {
            "fund": {
                "plus": float(total_plus_fund),
                "minus": float(total_minus_fund),
                "balance": float(total_plus_fund - total_minus_fund),
            },
            "bank": {
                "plus": float(total_plus_bank),
                "minus": float(total_minus_bank),
                "balance": float(total_plus_bank - total_minus_bank),
            }
        },
        "before_balance": {
            "fund": float(before_plus_fund - before_minus_fund),
            "bank": float(before_plus_bank - before_minus_bank),
            "total": float(
                (before_plus_fund - before_minus_fund) +
                (before_plus_bank - before_minus_bank)
            )
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_transactions_modfier(request):
    today = date.today()

    # 🔹 Dates par défaut = aujourd’hui
    start_date = request.GET.get("start_date", today)
    end_date = request.GET.get("end_date", today)

    # 🔹 Utilisateur par défaut = user connecté
    user_id = request.GET.get("user_id", request.user.id)

    # ---- Transactions dans l'intervalle ----
    transactions = Transaction.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date,
        user_id=user_id,
        month__isnull=True,
        is_adjustment=False
    ).order_by("date")

    serializer = TransactionSerializer(transactions, many=True)

    return Response({
        "results": serializer.data
    })


@api_view(['GET'])
def filter_transactions_account(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    account_id = request.GET.get("account_id")
    employee_id = request.GET.get("employee_id")
    bank_id = request.GET.get("bank_id")

    if not start_date or not end_date:
        return Response({"error": "Both start_date and end_date are required"}, status=400)

    # ---- Transactions dans l'intervalle ----
    transactions = Transaction.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date
    ).order_by("date")

    if account_id:
        transactions = transactions.filter(account_id=account_id)

    if employee_id:
        transactions = transactions.filter(employee_id=employee_id)

    if bank_id:
        transactions = transactions.filter(bank_id=bank_id)

    serializer = TransactionSerializer(transactions, many=True)

    # ---- Totaux période ----
    total_plus = transactions.filter(type="plus").aggregate(s=Sum("paid_amount"))["s"] or 0
    total_minus = transactions.filter(type="minus").aggregate(s=Sum("paid_amount"))["s"] or 0

    return Response({
        "transactions": serializer.data,
        "totals": {
            "plus": total_plus,
            "minus": total_minus
        },
    })


@api_view(['GET'])
def unpaid_students(request):
    branch_id = request.GET.get('branch_id')
    class_id = request.GET.get('class_id')
    year_id = request.GET.get('year_id')

    if not year_id:
        return Response({"error": "year_id est obligatoire"}, status=400)

    try:
        academic_year = AcademicYear.objects.get(id=year_id)
    except AcademicYear.DoesNotExist:
        return Response({"error": "année académique non trouvée"}, status=404)

    students = Etudiant.objects.filter(
        is_inscrire=1,
        payment_nature='mensuel'
        etat='inscrit', 
        is_active=True
    ).exclude(
        date_desectivation__isnull=False,
    )

    if branch_id:
        students = students.filter(branche_id=branch_id)
    if class_id:
        students = students.filter(classe_id=class_id)

    result = []
    today = date.today()

    for student in students:
        payments = Paiement.objects.filter(
            etudiant=student,
            academic_year=academic_year
        )

        total_unpaid = Decimal("0.00")
        months_unpaid = []

        start_date = max(student.date_inscription, academic_year.start_date)
        end_date = min(today, academic_year.end_date)

        current = date(start_date.year, start_date.month, 1)

        while current <= end_date:
            month_number = current.month
            month_name = ARABIC_MONTHS[month_number - 1]

            payments_for_month = payments.filter(month=month_number)

            # 🔑 S’IL Y A UN ENREGISTREMENT → ON FAIT CONFIANCE AU remaining_amount
            if payments_for_month.exists():
                month_remaining = sum(
                    Decimal(p.remaining_amount or 0)
                    for p in payments_for_month
                )
            else:
                # Pas de paiement du tout → mois totalement impayé
                month_remaining = Decimal(student.remaining or 0)

            if month_remaining > 0:
                months_unpaid.append(month_name)
                total_unpaid += month_remaining

            # mois suivant
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        if total_unpaid > 0:
            result.append({
                "id": student.id,
                "student_name": student.student_name,
                "branch_name": student.branche.nom,
                "class_name": student.classe.nom,
                "phone": student.agent.whatsapp_phone if student.agent and student.agent.whatsapp_phone else student.phone,
                "months_unpaid": ", ".join(months_unpaid),
                "unpaid_amount": float(total_unpaid),
                "date_inscription": student.date_inscription,
            })

    return Response(result)


@api_view(['GET'])
def class_payment_stats(request):
    branch_id = request.GET.get('branch_id')
    month = request.GET.get('month')  # obligatoire pour ton cas
    year_id = request.GET.get('year_id')

    if not month:
        return Response({"error": "month est obligatoire"}, status=400)
    today = date.today()
    target_month = int(month) if month else today.month

    students = Etudiant.objects.filter(
            is_inscrire=1, 
            payment_nature='mensuel', 
            etat='inscrit', 
            is_active=True
        ).exclude(
            date_desectivation__isnull=False,
        )
    if branch_id:
        students = students.filter(branche_id=branch_id)

    if year_id:
        try:
            academic_year = AcademicYear.objects.get(id=year_id)
        except AcademicYear.DoesNotExist:
            return Response({"error": "année académique non trouvée"}, status=404)
    else:
        academic_year = None

    class_stats = defaultdict(lambda: {
        "class_name": "",
        "total_students": 0,
        "total_due": 0.0,
        "total_paid": 0.0,
        "total_unpaid": 0.0,
    })

    for student in students:
        if not student.classe:
            continue

        classe_name = student.classe.nom
        monthly_fee = Decimal(student.remaining or 0)

        payments = Paiement.objects.filter(
            etudiant=student,
            month=target_month
        )

        if academic_year:
            payments = payments.filter(academic_year=academic_year)

        # 🔹 Calcul du montant dû pour CE MOIS SEULEMENT
        if (
            student.date_inscription.month == target_month and
            student.date_inscription.year == (academic_year.start_date.year if academic_year else student.date_inscription.year)
        ):
            days_in_month = monthrange(student.date_inscription.year, target_month)[1]
            remaining_days = days_in_month - student.date_inscription.day + 1
            month_due = monthly_fee * Decimal(remaining_days) / Decimal(days_in_month)
        else:
            month_due = monthly_fee

        if payments.exists():
            # 🔥 SOURCE DE VÉRITÉ
            month_remaining = sum(
                Decimal(p.remaining_amount or 0)
                for p in payments
            )
            month_unpaid = max(month_remaining, Decimal(0))
            month_paid = month_due - month_unpaid
        else:
            month_unpaid = month_due
            month_paid = Decimal(0)

        stats = class_stats[classe_name]
        stats["class_name"] = classe_name
        stats["total_students"] += 1
        stats["total_due"] += float(month_due)
        stats["total_paid"] += float(month_paid)
        stats["total_unpaid"] += float(month_unpaid)

    return Response(list(class_stats.values()))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_suspension(request):
    """
    Create a suspension record with unpaid months data
    Expected POST data:
    {
        "student_id": 3,
        "reason": "تأخر في الدفع",
        "suspend_date": "2026-01-27",
        "monthly_fee": 1200.00,
        "unpaid_months_data": [...]  # From unpaid_months_until_suspend endpoint
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['student_id', 'reason', 'suspend_date', 'monthly_fee', 'unpaid_months_data']
        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"الحقل '{field}' مطلوب"},
                    status=400
                )
        
        # Get student
        try:
            student = Etudiant.objects.get(id=data['student_id'])
        except Etudiant.DoesNotExist:
            return Response({"error": "الطالب غير موجود"}, status=404)
        
        # Parse dates and amounts
        try:
            suspend_date = date.fromisoformat(data['suspend_date'])
            monthly_fee = Decimal(str(data['monthly_fee']))
        except (ValueError, TypeError):
            return Response({"error": "تاريخ أو مبلغ غير صالح"}, status=400)
        
        # Calculate total unpaid from unpaid_months_data
        unpaid_months = data.get('unpaid_months_data', [])
        total_unpaid = sum(
            Decimal(str(month.get('remaining_amount', 0)))
            for month in unpaid_months
        )
        
        # Create suspension record
        with transaction.atomic():
            suspension = Suspension.objects.create(
                student=student,
                reason=data['reason'],
                suspend_date=suspend_date,
                monthly_fee=monthly_fee,
                total_unpaid=total_unpaid,
                unpaid_months_data=unpaid_months,
                created_by=request.user,
                notes=data.get('notes', '')
            )
            
            # Update student status (optional)
            student.is_suspended = True
            student.suspension_reason = data['reason']
            student.date_desectivation = suspend_date
            student.etat = "suspendu"
            student.save()
        
        # Serialize and return response
        serializer = SuspensionSerializer(suspension)
        
        return Response({
            "success": True,
            "message": "تم تعليق الطالب بنجاح",
            "suspension_id": suspension.id,
            "data": serializer.data
        })
        
    except Exception as e:
        return Response(
            {"error": f"حدث خطأ: {str(e)}"},
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reactivate_student(request, student_id):
    """
    Réactive un étudiant, même si aucune suspension n'existe.
    """
    try:
        student = Etudiant.objects.get(id=student_id)
        reactivation_date = date.fromisoformat(
            request.data.get('reactivation_date', date.today().isoformat())
        )

        # 🔹 Essayer de récupérer la suspension active
        try:
            suspension = Suspension.objects.get(student=student, status='active')
            unpaid_months = suspension.unpaid_months_data or []
            monthly_fee = suspension.monthly_fee or 0
            suspension_exists = True
        except Suspension.DoesNotExist:
            suspension = None
            unpaid_months = []
            monthly_fee = request.data.get('month_fee', 0)  # Optionnel si tu veux calculer les paiements
            suspension_exists = False

        created_count = 0

        # =====================================================
        # 1️⃣ Créer les Paiements si suspension existait
        # =====================================================
        for item in unpaid_months:
            month = int(item["month"])
            academic_year_label = item["academic_year"]

            academic_year = AcademicYear.objects.filter(year=academic_year_label).first()
            if not academic_year:
                continue

            due_amount = Decimal(str(item["due_amount"]))
            paid_amount = Decimal(str(item.get("paid_amount", 0)))
            remaining_amount = Decimal(str(item["remaining_amount"]))

            Paiement.objects.get_or_create(
                etudiant=student,
                academic_year=academic_year,
                month=month,
                defaults={
                    "due_amount": due_amount,
                    "paid_amount": paid_amount,
                    "remaining_amount": remaining_amount,
                    "user": request.user
                }
            )
            created_count += 1

        # =====================================================
        # 2️⃣ Mettre à jour la suspension si existait
        # =====================================================
        if suspension_exists:
            suspension.status = 'completed'
            suspension.reactivation_date = reactivation_date
            suspension.reactivation_reason = request.data.get(
                'reason', 'إعادة تنشيط الطالب'
            )
            suspension.save()

        # =====================================================
        # 3️⃣ Mettre à jour l'étudiant
        # =====================================================
        student.suspension_reason = ''
        student.date_desectivation = None
        student.date_inscription = reactivation_date
        student.etat = "inscrit"
        student.save()

        return Response({
            "success": True,
            "message": "تم إعادة تنشيط الطالب بنجاح",
            "months_restored": created_count,
            "suspension_exists": suspension_exists
        })

    except Etudiant.DoesNotExist:
        return Response({"error": "الطالب غير موجود"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


        