from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Branche, Classe, Niveau, Agent, Etudiant, Mois, Paiement, BankAccount, Receipt, ReceiptPayment, Utilisateur, Activity, AcademicYear, MonthlyReport, DailyAbsence
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view

from datetime import date
from calendar import monthrange
from decimal import Decimal


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Validation Error:", serializer.errors)
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    def get_queryset(self):
        queryset = Etudiant.objects.all()
        classe = self.request.query_params.get('classe')
        if classe:
            queryset = queryset.filter(classe_id=classe)
        return queryset

class MoisViewSet(viewsets.ModelViewSet):
    queryset = Mois.objects.all()
    serializer_class = MoisSerializer

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

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

    # Arabic month names
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]

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
    for month in range(1, 13):
        if month < registration_month:
            # Before registration month => considered paid
            status = "paid"
            status_bool = True
            due_amount = 0
            paid_amount = 0
            remaining_amount = 0

        elif month == registration_month:
            # Prorated month
            days_in_month = monthrange(student.date_inscription.year, month)[1]
            proportion = (days_in_month - registration_day + 1) / days_in_month
            full_month_fee = 100  # TODO: replace with real fee from Frais model
            due_amount = round(full_month_fee * proportion, 2)

            payment = payments_dict.get(month)
            if payment:
                paid_amount = payment['paid_amount']
                remaining_amount = Decimal(due_amount) - Decimal(paid_amount)

                if remaining_amount <= 0:
                    status = "paid"
                    status_bool = True
                elif paid_amount > 0:
                    status = "partial"
                    status_bool = False
                else:
                    status = "unpaid"
                    status_bool = False
            else:
                paid_amount = 0
                remaining_amount = due_amount
                status = "unpaid"
                status_bool = False

        else:
            # Normal month
            full_month_fee = 100  # TODO: replace with real fee from Frais model
            due_amount = full_month_fee
            payment = payments_dict.get(month)
            if payment:
                paid_amount = payment['paid_amount']
                remaining_amount = due_amount - paid_amount
                if remaining_amount <= 0:
                    status = "paid"
                    status_bool = True
                elif paid_amount > 0:
                    status = "partial"
                    status_bool = False
                else:
                    status = "unpaid"
                    status_bool = False
            else:
                paid_amount = 0
                remaining_amount = due_amount
                status = "unpaid"
                status_bool = False

        result.append({
            "month": month,
            "month_name_ar": arabic_months[month - 1],
            "status": status,
            "status_bool": status_bool,
            "due_amount": due_amount,
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount
        })

    return Response(result)
    