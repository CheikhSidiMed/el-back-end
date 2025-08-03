from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Branche, Classe, Niveau, Agent, Etudiant, Mois, Paiement, Utilisateur, Activity, AcademicYear, MonthlyReport, DailyAbsence
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view


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


