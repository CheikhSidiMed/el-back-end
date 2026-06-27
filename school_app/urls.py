from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()

router.register(r'branches', BrancheViewSet, basename="branche")
router.register(r'classes', ClasseViewSet, basename="classe")
router.register(r'levels', NiveauViewSet, basename="niveau")
router.register(r'agents', AgentViewSet, basename="agent")
router.register(r'etudiants', EtudiantViewSet, basename="etudiant")
router.register(r'activitys', ActivityViewSet, basename="activity")
router.register(r'mois', MoisViewSet, basename="mois")
router.register(r'paiements', PaiementViewSet, basename="paiement")
router.register(r'bank-accounts', BankAccountViewSet, basename="bank-account")
router.register(r'receipts', ReceiptViewSet, basename="receipt")
router.register(r'receipts-payment', ReceiptPaymentViewSet, basename="receipt-payment")
router.register(r'academic-years', AcademicYearViewSet, basename="academic-year")
router.register(r'monthly-report', MonthlyReportViewSet, basename="monthly-report")
router.register(r'evaluation-periods', EvaluationPeriodViewSet, basename="evaluation-period")
router.register(r'evaluation-results', EvaluationResultViewSet, basename="evaluation-result")
router.register(r'quarterly-report', QuarterlyReportViewSet, basename="quarterly-report")
router.register(r'daily-absence', DailyAbsenceViewSet, basename="daily-absence")

router.register(r'accounts', AccountViewSet, basename="account")
router.register(r'account-categorys', AccountCategoryViewSet, basename="account-category")

router.register(r'transactions', TransactionViewSet, basename="transaction")
router.register(r'employees', EmployeeViewSet, basename="employee")
router.register(r'salary-payments', SalaryPaymentViewSet, basename='salary-payment')

router.register(r'jobs', JobViewSet, basename="job")

router.register(r'utilisateurs', UtilisateurViewSet, basename="utilisateur")
router.register(r'inscriptions', InscriptionViewSet, basename="inscription")

router.register(r'garants', GarantViewSet, basename="garant")
router.register(r'garant-paiements', GarantPaiementViewSet, basename="garant-paiement")

router.register(r'permissions', PermissionViewSet, basename="permission")
router.register(r'suspensions', SuspensionViewSet, basename="suspension")
router.register(r'absence-activitys', AbsenceActivityViewSet, basename="absence-activity")
router.register(r'exams', ExamViewSet, basename="exam")
router.register(r'abs-elmhdaras', AbsElmhdaraViewSet, basename="abs-elmhdara")

# router.register(r'sabak-qurras', SabakQurraViewSet, basename="sabak-qurra")
# router.register(r'sabak-hakams', SabakHakamViewSet, basename="sabak-hakam")
# router.register(r'evaluations', EvaluationViewSet, basename="evaluation")

router.register('competitions', CompetitionViewSet, basename="competition")
router.register('tasfiyats', TasfiyaViewSet, basename="tasfiyat")
router.register('juges', JugeViewSet, basename="juge")
router.register('participants', ParticipantViewSet, basename="participant")
router.register('evaluations', EvaluationViewSet, basename="evaluation")
router.register('competition-levels', CompetitionLevelViewSet, basename="competition-level")
router.register('paiement-transations', PaiementTransationsViewSet, basename="paiement-transation")
router.register('etudiant-certifieds', EtudiantCertifiedViewSet, basename="etudiant-certifieds")
router.register('attestations', AttestationViewSet, basename="attestations")
router.register('exit-certificates', ExitCertificateViewSet, basename="exit-certificate")
router.register('evaluation-month-results', EvaluationMonthResultViewSet, basename="evaluation-month-result")
router.register('agent-portal', AgentPortalViewSet, basename="agent-portal")

urlpatterns = [
    path('', include(router.urls)),
    path('api/daily-absence/par-month', daily_absence_list, name='daily-absence-by-month'),
    path('api/daillys/filter/', filter_transactions, name='filter-dailly'),
    path('api/filter/transations-modifier/', filter_transactions_modfier, name='filter-dailly'),
    path('api/preview/filter/', filter_transactions_account, name='filter-dailly'),
    path('api/unpaid-students/', unpaid_students, name='unpaid-students'),
    path('api/unpaid-by-agent/', unpaid_by_agent, name='unpaid-by-agents'),
    path('api/unpaid-dont-have-agent/', unpaid_students_not_have_agent, name='unpaid-dont-have-agents'),
    path('api/class-stats/', class_payment_stats, name='class-stats'),
    path('api/attestation-certified-stats/', attestation_certified_stats, name='attestation-certified-stats'),
    path('api/student/payments/', student_payments, name='student-payments'),
    
    path('api/student-by-level/', student_by_level, name='student-by-levels'),
    path('api/student/unpaid-months/', unpaid_months_until_suspend, name='student-unpaid-months'),
    path('api/garant/payments/', garant_payments, name='garant-payments'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('api-auth/', include('rest_framework.urls')),
    path('api/register/', RegisterUserView.as_view(), name='register_user'),
    path('api/role-permissions/<str:role_code>/', RolePermissionsView.as_view(), name='role-permissions'),
    path('api/permissions-tree/', PermissionTreeAPIView.as_view(), name='permissions-tree'),
    path('api/etudents-count-by-classes/<int:classe_id>/', ClasseEffectifAPIView.as_view(), name='etudents-count-by-classe'),
    path('api/suspensions-create/', create_suspension, name='suspension-create'),
    path('api/suspensions-reactivate/<int:student_id>/', reactivate_student, name='suspension-reactivate'),
    path("api/bank-transfer/", BankTransferView.as_view(), name="bank-transfer"),
    path('participant/assign/', assign_participants, name='assign-participants'),
    path('api/participant-by-competition/', participants_by_competition, name='participants-by-competition'),
    path('api/tasfiyat-by-competition/', tasfiyats_by_competition, name='tasfiyats-by-competition'),
    path('participants-autocomplite/', participants_autocomplete, name='participants-autocomplite'),
    path('participants-list/', participants_list, name='participants-lists'),
    path('get-receipt-by-id/', get_receipt_by_id, name='get-receipt-by-id'),
    path('get-last-receipt/', get_last_receipt, name='get-last-receipt'),
    path('get-last-agent-receipt/', get_last_agent_receipt, name='get-last-agent-receipts'),


]
