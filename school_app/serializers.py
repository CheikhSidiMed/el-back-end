from rest_framework import serializers
from .models import Branche, Classe, Niveau, Agent, Etudiant, Mois, Paiement, Inscription, Garant, GarantPaiement, SalaryPayment, Employee, Job, BankAccount, Receipt, ReceiptPayment, Utilisateur, Activity, AcademicYear, MonthlyReport, DailyAbsence, AccountCategory, Account, Transaction, Permission
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class BrancheSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branche
        fields = '__all__'

class ClasseSerializer(serializers.ModelSerializer):
    # → visible UNIQUEMENT dans la réponse (GET)
    branche = BrancheSerializer(read_only=True)

    # → utilisé UNIQUEMENT à la création / mise à jour (POST / PATCH)
    branche_id = serializers.PrimaryKeyRelatedField(
        source='branche',                 # fait le lien avec le FK `branche`
        queryset=Branche.objects.all(),
        write_only=True
    )

    class Meta:
        model = Classe
        fields = ['id', 'nom', 'niveau', 'branche', 'branche_id']


class NiveauSerializer(serializers.ModelSerializer):
    class Meta:
        model = Niveau
        fields = '__all__'

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'

class EtudiantSerializer(serializers.ModelSerializer):
    level = NiveauSerializer(read_only=True)
    classe = ClasseSerializer(read_only=True)
    branche = BrancheSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)

    level_id = serializers.PrimaryKeyRelatedField(
        queryset=Niveau.objects.all(), source='level', write_only=True, required=False, allow_null=True
    )
    classe_id = serializers.PrimaryKeyRelatedField(
        queryset=Classe.objects.all(), source='classe', write_only=True, required=False, allow_null=True
    )
    branche_id = serializers.PrimaryKeyRelatedField(
        queryset=Branche.objects.all(), source='branche', write_only=True, required=False, allow_null=True
    )
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), source='agent', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Etudiant
        fields = '__all__'

class MoisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mois
        fields = '__all__'

class GarantPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarantPaiement
        fields = '__all__'

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'

class ReceiptPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptPayment
        fields = '__all__'

class MonthlyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyReport
        fields = '__all__'

class DailyAbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyAbsence
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'

class AccountCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountCategory
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    category = AccountCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=AccountCategory.objects.all(),
        source="category",
        write_only=True
    )
    class Meta:
        model = Account
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    branche = BrancheSerializer(read_only=True)
    branche_id = serializers.PrimaryKeyRelatedField(
        queryset=Branche.objects.all(), source='branche', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Employee
        fields = '__all__'

    def create(self, validated_data):
        employee = super().create(validated_data)

        Utilisateur.objects.create(
            phone=employee.phone,
            role=employee.job,  # associer au job comme role
            first_name=employee.full_name,  # pour cohérence
            password=employee.phone  # mot de passe par défaut
        )

        return employee

class SalaryPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SalaryPayment
        fields = '__all__'

# class PermissionSerializer(serializers.ModelSerializer):
#     children = serializers.SerializerMethodField()

#     class Meta:
#         model = Permission
#         fields = ['id', 'code', 'label', 'parent', 'children']

#     def get_children(self, obj):
#         job_permissions = self.context.get('job_permissions')

#         if not job_permissions:
#             return []

#         # فقط الأطفال الممنوحون فعليًا
#         children = obj.children.filter(id__in=job_permissions)

#         return PermissionSerializer(
#             children,
#             many=True,
#             context=self.context
#         ).data

class PermissionSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ['id', 'code', 'label', 'parent', 'children']

    def get_children(self, obj):
        job_permissions = self.context.get('job_permissions')

        if not job_permissions:
            return []

        children = obj.children.filter(id__in=job_permissions)

        return PermissionSerializer(
            children,
            many=True,
            context=self.context
        ).data


# class JobSerializer(serializers.ModelSerializer):
#     permissions = PermissionSerializer(many=True, read_only=True)
#     permission_ids = serializers.PrimaryKeyRelatedField(
#         queryset=Permission.objects.all(),
#         many=True,
#         write_only=True,
#         source='permissions'
#     )

#     class Meta:
#         model = Job
#         fields = [
#             'id',
#             'title',
#             'description',
#             'permissions',      # للعرض
#             'permission_ids',   # للإضافة
#         ]
#     def get_permissions(self, obj):
#         job_permissions = obj.permissions.values_list('id', flat=True)

#         roots = obj.permissions.filter(parent__isnull=True)

#         return PermissionSerializer(
#             roots,
#             many=True,
#             context={'job_permissions': job_permissions}
#         ).data

class JobSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions'
    )

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'description',
            'permissions',      # for display
            'permission_ids',   # for create/update
        ]

    def get_permissions(self, obj):
        job_permissions = obj.permissions.values_list('id', flat=True)

        roots = Permission.objects.filter(
            parent__isnull=True,
            id__in=job_permissions
        )

        return PermissionSerializer(
            roots,
            many=True,
            context={'job_permissions': job_permissions}
        ).data

class PermissionTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ['id', 'code', 'label', 'children']

    def get_children(self, obj):
        children = obj.children.all()
        return PermissionTreeSerializer(children, many=True).data
        
class InscriptionSerializer(serializers.ModelSerializer):
    student = EtudiantSerializer(read_only=True)
    activity = ActivitySerializer(read_only=True)

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(), source='student', write_only=True, required=False
    )
    activity_id = serializers.PrimaryKeyRelatedField(
        queryset=Activity.objects.all(), source='activity', write_only=True, required=False
    )
    class Meta:
        model = Inscription
        fields = '__all__'

class GarantSerializer(serializers.ModelSerializer):
    account = AccountSerializer(read_only=True)

    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(), source='account', write_only=True, required=False
    )
    class Meta:
        model = Garant
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    bank = BankAccountSerializer(read_only=True)
    bank_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(), source='bank', write_only=True, required=True
    )
    agent = AgentSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), source='agent', write_only=True, required=False
    )
    garant = GarantSerializer(read_only=True)
    garant_id = serializers.PrimaryKeyRelatedField(
        queryset=Garant.objects.all(), source='garant', write_only=True, required=False
    )
    student = EtudiantSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(), source='student', write_only=True, required=False
    )
    account = AccountSerializer(read_only=True)
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(), source='account', write_only=True, required=False
    )
    employee = EmployeeSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='employee', write_only=True, required=False
    )
    garant = GarantSerializer(read_only=True)
    garant_id = serializers.PrimaryKeyRelatedField(
        queryset=Garant.objects.all(), source='garant', write_only=True, required=False
    )
    inscription = InscriptionSerializer(read_only=True)
    inscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Inscription.objects.all(), source='inscription', write_only=True, required=False
    )
    receipt_id = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'
        
    def get_receipt_id(self, obj):
        receipt_payment = obj.receipt_payments.first()
        return receipt_payment.receipt.receipt_id if receipt_payment else None

class UtilisateurRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ['phone', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UtilisateurSerializer(serializers.ModelSerializer):
    role = JobSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        source="role",
        write_only=True
    )
    class Meta:
        model = Utilisateur
        fields = ['id', 'phone', 'role', 'role_id', 'first_name', 'password', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'created_at': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Utilisateur(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: Utilisateur):
        token = super().get_token(user)
        # you can add custom claims if you like:
        # token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Now inject the serialized user data into the response:
        data['user'] = UtilisateurSerializer(self.user).data
        return data

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AcademicYear
        fields = ("id", "year", "start_date", "end_date")


class PaiementSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), source='agent', write_only=True, required=False
    )
    etudiant = EtudiantSerializer(read_only=True)
    etudiant_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(), source='etudiant', write_only=True, required=False
    )
    academic_year = AcademicYearSerializer(read_only=True)
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source='academic_year', write_only=True, required=False
    )
    bank = BankAccountSerializer(read_only=True)
    bank_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(), source='bankAccount', write_only=True, required=False
    )
    user = UtilisateurSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(), source='user', write_only=True, required=False
    )
    class Meta:
        model = Paiement
        fields = '__all__'
