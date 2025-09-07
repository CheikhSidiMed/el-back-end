from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Branche, Classe, Niveau, Agent, Receipt, ReceiptPayment, Job, Employee, Transaction, Etudiant, Mois, Paiement, BankAccount, Receipt, ReceiptPayment, Utilisateur, Activity, AcademicYear, MonthlyReport, DailyAbsence, AccountCategory, Account
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view
from django.db import transaction
from rest_framework.permissions import IsAuthenticated

from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from django.utils import timezone
from datetime import date, datetime

from calendar import monthrange
from decimal import Decimal
from rest_framework import status

class BrancheViewSet(viewsets.ModelViewSet):
    queryset = Branche.objects.all()
    serializer_class = BrancheSerializer

class ClasseViewSet(viewsets.ModelViewSet):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializer

class NiveauViewSet(viewsets.ModelViewSet):
    queryset = Niveau.objects.all()
    serializer_class = NiveauSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

class EtudiantViewSet(viewsets.ModelViewSet):
    queryset = Etudiant.objects.all()
    serializer_class = EtudiantSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent_id'] 

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
            student=None,
            agent=None,
            account=transaction.account,
            employee=None,
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


class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated] 

    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        """
        Process payment: use single-student logic if no agent, multi-student logic if agent exists.
        """
        data = request.data
        agent_id = data.get("agent")
        payments = data.get("payments")  # list of {student, month, due_amount, paid_amount}
        payment_method = data.get("payment_method")
        bank_id = data.get("bank")

        if not payments:
            return Response({"error": "No payments provided"}, status=400)

        with transaction.atomic():
            if not agent_id:
                # --- Paiement sans agent (pour un seul étudiant) ---
                student_id = data.get("student")
                if not student_id:
                    return Response({"error": "No student provided for payment"}, status=400)
                student = Etudiant.objects.get(id=student_id)

                receipt = Receipt.objects.create(
                    student=student,
                    agent_id=None,
                    total_amount=sum([p["paid_amount"] for p in payments]),
                    receipt_date=timezone.now(),
                    created_by=request.user,
                    receipt_description="Paiement des frais de scolarité"
                )

                created_transactions = []
                for p in payments:
                    # 🔹 check if this month already has a Paiement
                    existing = Paiement.objects.filter(
                        etudiant=student,
                        academic_year_id=p.get("academic_year"),
                        month=p["month"]
                    ).order_by("-id").first()

                    if existing:
                        new_paid = existing.paid_amount + p["paid_amount"]
                        new_remaining = max(0, p["due_amount"] - new_paid)
                    else:
                        new_paid = p["paid_amount"]
                        new_remaining = max(0, p["due_amount"] - new_paid)

                    txn = Transaction.objects.create(
                        student=student,
                        agent_id=None,
                        month=p["month"],
                        due_amount=p["due_amount"],
                        paid_amount=p["paid_amount"],  # this transaction only
                        remaining_amount=new_remaining,
                        date=timezone.now(),
                        payment_method=payment_method,
                        bank_id=bank_id,
                        user=request.user
                    )

                    ReceiptPayment.objects.create(receipt=receipt, transaction=txn)

                    Paiement.objects.create(
                        etudiant=student,
                        academic_year_id=p.get("academic_year"),
                        month=p["month"],
                        due_amount=p["due_amount"],
                        paid_amount=new_paid,        # 🔹 cumulative paid
                        remaining_amount=new_remaining,
                        payment_method=payment_method,
                        bank_id=bank_id,
                        agent_id=None,
                        user=request.user
                    )

                    created_transactions.append(txn.id)

            else:
                # --- Paiement avec agent (plusieurs étudiants) ---
                total_paid = sum([p["paid_amount"] for p in payments])
                receipt = Receipt.objects.create(
                    student=None,
                    agent_id=agent_id,
                    total_amount=total_paid,
                    receipt_date=timezone.now(),
                    created_by=request.user,
                    receipt_description="Paiement des frais de scolarité pour plusieurs étudiants"
                )

                created_transactions = []
                for p in payments:
                    student = Etudiant.objects.get(id=p["student"])

                    # 🔹 check if this month already has a Paiement
                    existing = Paiement.objects.filter(
                        etudiant=student,
                        academic_year_id=p.get("academic_year"),
                        month=p["month"]
                    ).order_by("-id").first()

                    if existing:
                        new_paid = existing.paid_amount + Decimal(str(p["paid_amount"]))
                        new_remaining = max(Decimal('0.0'), Decimal(str(p["due_amount"])) - new_paid)
                    else:
                        new_paid = Decimal(str(p["paid_amount"]))
                        new_remaining = max(Decimal('0.0'), Decimal(str(p["due_amount"])) - new_paid)

                    txn = Transaction.objects.create(
                        student=student,
                        agent_id=agent_id,
                        month=p["month"],
                        due_amount=p["due_amount"],
                        paid_amount=p["paid_amount"],  # this transaction only
                        remaining_amount=new_remaining,
                        date=timezone.now(),
                        payment_method=payment_method,
                        bank_id=bank_id,
                        user=request.user
                    )

                    ReceiptPayment.objects.create(receipt=receipt, transaction=txn)

                    Paiement.objects.create(
                        etudiant=student,
                        academic_year_id=p.get("academic_year"),
                        month=p["month"],
                        due_amount=p["due_amount"],
                        paid_amount=new_paid,        # 🔹 cumulative paid
                        remaining_amount=new_remaining,
                        payment_method=payment_method,
                        bank_id=bank_id,
                        agent_id=agent_id,
                        user=request.user
                    )

                    created_transactions.append(txn.id)

        return Response({
            "message": "Paiement traité avec succès",
            "receipt_id": receipt.pk,
            "receipt_date": receipt.receipt_date.strftime("%Y-%m-%d | %H:%M:%S"),
            "transactions": created_transactions,
            "created_by": request.user.first_name,
        })


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer


class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer


class ReceiptPaymentViewSet(viewsets.ModelViewSet):
    queryset = ReceiptPayment.objects.all()
    serializer_class = ReceiptPaymentSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class DailyAbsenceViewSet(viewsets.ModelViewSet):
    queryset = DailyAbsence.objects.all()
    serializer_class = DailyAbsenceSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


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

    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('password')
        if new_password:
            user.set_password(new_password)
            user.save()
            return Response({'status': 'password updated'})
        return Response({'error': 'Password not provided'}, status=400)
        

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class AcademicYearViewSet(viewsets.ModelViewSet):
    """Full CRUD for AcademicYear (list, retrieve, create, update, delete)."""
    queryset         = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    lookup_field     = "id"


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

    # Validate student + year
    try:
        student = Etudiant.objects.get(id=student_id)
        academic_year = AcademicYear.objects.get(id=year_id)
    except (Etudiant.DoesNotExist, AcademicYear.DoesNotExist):
        return Response({"error": "Invalid student or academic year"}, status=400)

    registration_month = student.date_inscription.month
    registration_day = student.date_inscription.day

    # Get all recorded payments
    payments = Paiement.objects.filter(
        etudiant=student,
        academic_year=academic_year
    ).values('month', 'due_amount', 'paid_amount', 'remaining_amount')

    payments_dict = {p['month']: p for p in payments}

    result = []
    for month in range(1, 12 + 1):
        if month < registration_month:
            # Before registration month => considered paid
            status = "paid"
            status_bool = True
            due_amount = Decimal("0.00")
            paid_amount = Decimal("0.00")
            remaining_amount = Decimal("0.00")

        elif month == registration_month:
            # Prorated month
            days_in_month = monthrange(student.date_inscription.year, month)[1]
            proportion = Decimal(days_in_month - registration_day + 1) / Decimal(days_in_month)
            due_amount = (full_month_fee * proportion).quantize(Decimal("0.01"))

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

        else:
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



from django.db.models.signals import post_save
from django.dispatch import receiver

# from .models import Transaction


@receiver(post_save, sender=Transaction)
def update_account_balance(sender, instance, created, **kwargs):
    if created and instance.bank:
        if instance.type == "plus":  # Crédit
            instance.bank.balance += instance.paid_amount
        elif instance.type == "minus":  # Débit
            instance.bank.balance -= instance.paid_amount
        instance.bank.save()
    if created and instance.account:
        if instance.type == "plus":  # Crédit
            instance.account.balance += instance.paid_amount
        elif instance.type == "minus":  # Débit
            instance.account.balance -= instance.paid_amount
        instance.account.save()
    if created and instance.employee:
        if instance.type == "plus":  # Crédit
            instance.employee.balance += instance.paid_amount
        elif instance.type == "minus":  # Débit
            instance.employee.balance -= instance.paid_amount
        instance.employee.save()
