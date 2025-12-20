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

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/daily-absence/par-month', daily_absence_list, name='daily-absence-by-month'),
    path('api/daillys/filter/', filter_transactions, name='filter-dailly'),
    path('api/preview/filter/', filter_transactions_account, name='filter-dailly'),
    path('api/unpaid-students/', unpaid_students, name='unpaid-students'),
    path('api/class-stats/', class_payment_stats, name='class-stats'),
    path('api/student/payments/', student_payments, name='student-payments'),
    path('api/student/unpaid-months/', unpaid_months_until_suspend, name='student-unpaid-months'),
    path('api/garant/payments/', garant_payments, name='garant-payments'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('api-auth/', include('rest_framework.urls')),
    path('api/register/', RegisterUserView.as_view(), name='register_user'),
    path('api/role-permissions/<str:role_code>/', RolePermissionsView.as_view(), name='role-permissions'),
    path('api/permissions-tree/', PermissionTreeAPIView.as_view(), name='permissions-tree'),
    path('api/etudents-count-by-classes/<int:classe_id>/', ClasseEffectifAPIView.as_view(), name='etudents-count-by-classe'),
    path('api/suspensions/create/', create_suspension, name='suspensions-create'),
    path('api/suspensions/<int:classe_id>/reactivate/', reactivate_student, name='suspensions-reactivate'),
]
