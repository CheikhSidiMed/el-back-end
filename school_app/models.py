from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import date
from django.contrib.postgres.fields import JSONField 
from django.db.models import JSONField
from django.db.models import Max
import uuid
import os

def upload_student_photo(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('etudiants/', filename)

def get_default_academic_year():
    return AcademicYear.objects.order_by('-start_date').first()

def get_default_academic_year_receipt():
    year = AcademicYear.objects.first()
    return year.id if year else None
    
class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=150)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    def __str__(self):
        return self.label

class Job(models.Model):
    ROLES = (
        ('admin_g', 'مدير عام'),
        ('admin', 'مدير التسجيل والحسابات'),
        ('dg_lessen', 'مدير الدروس'),
        ('admin_m', 'إدارة المقرأة'),
        ('teacher', 'أستاذ(ة)'),
        ('user', 'مراقب'),
        ('worker', 'عامل'),
        ('hakam', 'حكم'),
    )
    title = models.CharField(max_length=150, choices=ROLES, unique=True, default='user')
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.title      

class Branche(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.TextField()

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Branche"
        verbose_name_plural = "Branches"

class UtilisateurManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Le numéro de téléphone est requis")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)

class Utilisateur(AbstractUser):

    role = models.ForeignKey(
        'Job',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='utilisateur'
    )
    branches = models.ManyToManyField(Branche, blank=True)
    classe = models.ForeignKey('Classe', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_class')
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    username = None
    last_name = None
    email = None

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UtilisateurManager()

    def get_full_name(self):
        """
        Retourne le nom complet lisible
        """
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name if full_name else self.phone

    def __str__(self):
        return self.phone or "Utilisateur sans numéro"

class Classe(models.Model):
    nom = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50, null=True, blank=True)
    branche = models.ForeignKey(Branche, on_delete=models.CASCADE, related_name='classes', null=True, blank=True )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.nom} - {self.niveau}"

class Niveau(models.Model):
    level_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.level_name

class Agent(models.Model):
    agent_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    phone_2 = models.CharField(max_length=20, null=True, blank=True)
    profession = models.CharField(max_length=100, null=True, blank=True)
    whatsapp_phone = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        ordering = ['-id'] 

    def __str__(self):
        return self.agent_name

class Etudiant(models.Model):
    student_name = models.CharField(max_length=100)
    part_count = models.PositiveIntegerField(default=1)
    is_inscrire = models.PositiveIntegerField(default=1)  # 1 = inscrit, 0 = not inscrit
    gender = models.CharField(max_length=1, choices=[('M', 'ذكر'), ('F', 'أنثى')])
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=100, null=True, blank=True)
    nni = models.CharField(max_length=100, null=True, blank=True)
    date_inscription = models.DateField(default=date.today)
    date_count = models.DateField(auto_now_add=True)
    student_photo = models.ImageField(upload_to=upload_student_photo, null=True, blank=True)

    payment_nature = models.CharField(
        max_length=20,
        choices=[('free', 'Gratuit'), ('mensuel', 'Mensuel')],
        default='mensuel'
    )

    fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    remaining = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    classe = models.ForeignKey('Classe', null=True, blank=True, on_delete=models.CASCADE, related_name='etudiants')
    branche = models.ForeignKey('Branche', null=True, blank=True, on_delete=models.CASCADE)
    agent = models.ForeignKey('Agent', null=True, blank=True, on_delete=models.SET_NULL)

    phone = models.CharField(max_length=20, null=True, blank=True)
    level = models.ForeignKey('Niveau', null=True, blank=True, on_delete=models.SET_NULL)

    rewaya = models.CharField(max_length=50, null=True, blank=True)
    days = models.CharField(max_length=200, null=True, blank=True)
    tdate = models.CharField(max_length=60, null=True, blank=True)
    start = models.CharField(max_length=200, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    elmoutoune = models.CharField(max_length=20, null=True, blank=True)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    date_desectivation = models.DateField(null=True, blank=True)
    suspension_reason = models.TextField(null=True, blank=True)

    current_city = models.CharField(max_length=100, null=True, blank=True)
    etat = models.CharField(
        max_length=50,
        choices=[('inscrit', 'Inscrit'), ('suspendu', 'Suspendu'), ('en_attente', 'En attente')],
        default='inscrit'
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.student_name

    def save(self, *args, **kwargs):
        # If level is set and payment is not free
        if self.level and self.payment_nature != 'free':
            self.fees = self.level.price
        else:
            self.fees = 0
        
        # Compute remaining
        self.remaining = max(self.fees - self.discount, 0)

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.student_name

class Mois(models.Model):
    numero = models.IntegerField()
    annee = models.IntegerField()
    nom = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nom} {self.annee}"

    class Meta:
        unique_together = ('numero', 'annee')
        ordering = ['-annee', 'numero']

class Frais(models.Model):
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    branche = models.ForeignKey(Branche, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.classe.nom} - {self.montant} MRU"

class Activity(models.Model):

    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('completed', 'منتهية'),
    ]

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    session = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.session})"

class AcademicYear(models.Model):
    year        = models.CharField(max_length=9, unique=True, help_text="ex: 2024-2025")
    name        = models.CharField(max_length=9, default='2025', help_text="2025")
    start_date  = models.DateField()
    end_date    = models.DateField()

    class Meta:
        ordering            = ("-start_date",)
        verbose_name        = "Academic year"
        verbose_name_plural = "Academic years"

    def __str__(self) -> str:
        return self.year

    def clean(self):
        """extra integrity: end_date must be after start_date"""
        from django.core.exceptions import ValidationError
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

class MonthlyReport(models.Model):
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    year = models.CharField(max_length=20)
    month = models.CharField(max_length=20)

    ahzab = models.CharField(max_length=100, blank=True, null=True)
    thmn = models.CharField(max_length=100, blank=True, null=True)
    memorization_amount = models.CharField(max_length=100, blank=True, null=True)
    previous_level = models.CharField(max_length=100, blank=True, null=True)
    current_level = models.CharField(max_length=100, blank=True, null=True)
    progress = models.CharField(max_length=100, blank=True, null=True)
    absence = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'month', 'year']  # to avoid duplicates

    def __str__(self):
        return f"{self.student.full_name} - {self.month} {self.year}"

class QuarterlyReport(models.Model):
    QUARTER_CHOICES = [
        ('Q1', 'الفصل الأول'),
        ('Q2', 'الفصل الثاني'),
        ('Q3', 'الفصل الثالث'),
        ('Q4', 'الفصل الرابع'),
    ]
    
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE)

    year = models.CharField(max_length=20)
    quarter = models.CharField(max_length=2, choices=QUARTER_CHOICES)
    # quarter = models.CharField(max_length=20)  # الفصل الأول / الثاني ...

    # Month 1
    month_1_income = models.IntegerField(default=0)
    month_1_absence = models.IntegerField(default=0)

    # Month 2
    month_2_income = models.IntegerField(default=0)
    month_2_absence = models.IntegerField(default=0)

    # Month 3
    month_3_income = models.IntegerField(default=0)
    month_3_absence = models.IntegerField(default=0)

    # Totals
    total_income = models.IntegerField(default=0)
    total_absence = models.IntegerField(default=0)

    # Other fields
    total_ahzab = models.IntegerField(default=0)  # عدد الأحزاب
    extra = models.CharField(max_length=100, blank=True, null=True)  # زيادة المتون
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'quarter', 'year']

    def save(self, *args, **kwargs):
        # Auto-calculate totals
        self.total_income = (
            self.month_1_income +
            self.month_2_income +
            self.month_3_income
        )

        self.total_absence = (
            self.month_1_absence +
            self.month_2_absence +
            self.month_3_absence
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.quarter} {self.year}"

class DailyAbsence(models.Model):
    SESSION_CHOICES = [
        ('صباحًا', 'صباحًا'),
        ('مساءً', 'مساءً'),
    ]

    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    date = models.DateField()  # full date (e.g., 2025-07-16)
    currentYear = models.TextField(blank=True, null=True, default="2024-2025")
    session = models.CharField(max_length=6, choices=SESSION_CHOICES)  # AM or PM

    justified_absence = models.BooleanField(default=False)
    remark = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'date', 'session']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.get_session_display()})"

class EvaluationResult(models.Model):
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    year = models.CharField(max_length=20)
    month = models.CharField(max_length=20)

    evaluation = models.CharField(max_length=100, blank=True, null=True)
    elhasila = models.CharField(max_length=100, blank=True, null=True)
    progress = models.CharField(max_length=100, blank=True, null=True)
    result = models.CharField(max_length=100, blank=True, null=True)
    evaluation_final = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='evaluationresult'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'month', 'year']

    def __str__(self):
        return f"{self.student.full_name} - {self.month} {self.year}"

class Employee(models.Model):
    number = models.CharField(max_length=50, unique=True, blank=True, null=True)  # matricule ou code employé
    full_name = models.CharField(max_length=200)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    phone = models.CharField(max_length=30, blank=True, null=True)
    classe = models.ForeignKey(
        'Classe',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employees'
    )
    branche = models.ForeignKey(
        'Branche',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employees'
    )
    job = models.ForeignKey(
        'Job',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employees'
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee")
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    subscription_date = models.DateField()
    is_actif = models.BooleanField(default=True) 
    id_number = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        if not self.number:
            last_number = (
                Employee.objects
                .exclude(number__isnull=True)
                .exclude(number="")
                .aggregate(max_num=Max('number'))
                ['max_num']
            )

            if last_number and last_number.isdigit():
                self.number = str(int(last_number) + 1)
            else:
                self.number = "1"

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} ({self.number})"

class SalaryPayment(models.Model):
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='salary_payments'
    )
    academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.CASCADE,
        related_name='salary_payments'
    )
    month = models.PositiveSmallIntegerField(
        choices=[(i, f"{i:02d}") for i in range(1, 13)],
        help_text="Mois du paiement (1-12)"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Paiement de salaire"
        verbose_name_plural = "Paiements de salaires"
        ordering = ['-academic_year', '-month']
        # 🔒 Empêche deux salaires pour le même employé le même mois et année
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'academic_year', 'month'],
                name='unique_salary_per_employee_month_year'
            )
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.month:02d}/{self.academic_year}"

class BankAccount(models.Model):
    CATEGORY = (
        (1, 'صندوق'),
        (2, 'بنك'),
    )
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=13, decimal_places=2, default=0)
    category = models.CharField(choices=CATEGORY, null=True, blank=True, default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_accounts')
        
    class Meta:
        ordering = ['id']
        # ordering = ['-id'] 

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class Paiement(models.Model):

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    month = models.IntegerField()
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    bank = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.etudiant.student_name} - Mois: {self.month} - {self.academic_year.year}"

class AccountCategory(models.Model):
    """
    Catégorie de compte (ex: Banque, Caisse, Mobile Money, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Account(models.Model):
    """
    Compte bancaire / caisse / mobile money, etc.
    """
    category = models.ForeignKey(AccountCategory, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=150)
    number = models.CharField(max_length=50, blank=True, null=True)  # Numéro de compte / IBAN
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default="MRO")  # Exemple: MRO, EUR, USD
    date_opened = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.category})"

class Inscription(models.Model):
    """Join table with extra fields for a student's registration to an activity"""
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="inscription")
    montant = models.DecimalField(max_digits=8, decimal_places=2)  # amount paid
    montant_pay = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date_inscription = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'activity')

    def __str__(self):
        return f"{self.student} → {self.activity} ({self.montant})"

class Garant(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date_c = models.DateField(auto_now_add=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} → {self.account} ({self.montant})"

class GarantPaiement(models.Model):

    garant = models.ForeignKey(Garant, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    month = models.IntegerField()
    des = models.CharField(max_length=250)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    bank = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.garant.name} - Mois: {self.month} - {self.academic_year.year}"

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('plus', 'Plus'),
        ('minus', 'Minus'),
    ]

    student = models.ForeignKey(
        'Etudiant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    agent = models.ForeignKey(
        'Agent',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    month = models.TextField(blank=True, null=True) 
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sold_emp = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    date = models.DateTimeField(default=timezone.now)

    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='plus')

    bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    account = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    inscription = models.ForeignKey(
        'Inscription',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    garant = models.ForeignKey(
        'Garant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transactions'
    )
    related_transaction = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="adjustments"
    )
    is_adjustment = models.BooleanField(default=False)
    is_paiy_month = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Transaction {self.id} - {self.paid_amount}"

class Receipt(models.Model):
    receipt_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        'Etudiant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    agent = models.ForeignKey(
        'Agent',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    account = models.ForeignKey(
        'Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    garant = models.ForeignKey(
        'Garant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    receipt_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_receipts'
    )
    receipt_description = models.TextField(blank=True, null=True)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='receipt',
        default=get_default_academic_year_receipt
    )

    class Meta:
        ordering = ['-receipt_id']

    def __str__(self):
        return f"Receipt {self.receipt_id} - {self.total_amount}"

class ReceiptPayment(models.Model):
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='receipt_payments'
    )
    transaction = models.ForeignKey(
        'Transaction',
        on_delete=models.CASCADE,
        related_name='receipt_payments'
    )

    class Meta:
        unique_together = ('receipt', 'transaction')

    def __str__(self):
        return f"ReceiptPayment: Receipt {self.receipt_id} - Transaction {self.transaction.id}"

class PaiementTransations(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    bank = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    receipt = models.ForeignKey( Receipt, on_delete=models.CASCADE, related_name='receipt_paymentTransations')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created at')

    def __str__(self):
        return f"{self.etudiant.student_name} - Mois: {self.month} - {self.academic_year.year}"

class Suspension(models.Model):
    """Model to store student suspension information with unpaid months details"""
    
    SUSPENSION_STATUS = [
        ('active', 'معلق فعلياً'),
        ('completed', 'تم إنهاء التعليق'),
        ('cancelled', 'ملغي'),
    ]
    
    student = models.ForeignKey(
        'Etudiant', 
        on_delete=models.CASCADE,
        related_name='suspensions',
        verbose_name='الطالب'
    )
    
    # Basic suspension info
    reason = models.TextField(verbose_name='سبب التعليق')
    suspend_date = models.DateField(verbose_name='تاريخ التعليق')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    created_by = models.ForeignKey(
        'Utilisateur', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تم التعليق بواسطة'
    )
    
    # Unpaid months summary
    total_unpaid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='إجمالي المبلغ المتبقي'
    )
    
    # Detailed unpaid months data (stored as JSON)
    unpaid_months_data = JSONField(
        default=list,
        verbose_name='تفاصيل الأشهر غير المدفوعة'
    )
    
    # Student fee info at time of suspension
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='القسط الشهري وقت التعليق'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=SUSPENSION_STATUS,
        default='active',
        verbose_name='حالة التعليق'
    )
    
    # Reactivation info (if suspension ends)
    reactivation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ إعادة التنشيط'
    )
    
    reactivation_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='سبب إعادة التنشيط'
    )
    
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='ملاحظات إضافية'
    )
    
    class Meta:
        verbose_name = 'تعليق طالب'
        verbose_name_plural = 'تعليقات الطلاب'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['suspend_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"تعليق {self.student} - {self.suspend_date}"
    
    def save(self, *args, **kwargs):
        # Calculate total unpaid if not set
        if not self.total_unpaid and self.unpaid_months_data:
            total = sum(Decimal(str(month.get('remaining_amount', 0))) 
                       for month in self.unpaid_months_data)
            self.total_unpaid = total
        super().save(*args, **kwargs)
    
    def get_unpaid_months_count(self):
        """Return number of unpaid months"""
        return len(self.unpaid_months_data) if self.unpaid_months_data else 0
    
    def get_academic_years_affected(self):
        """Return unique academic years in unpaid months"""
        if not self.unpaid_months_data:
            return []
        years = set(month['academic_year'] for month in self.unpaid_months_data)
        return sorted(list(years))
    
    @property
    def is_active(self):
        return self.status == 'active'

class AbsenceActivity(models.Model):
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='absences'
    )

    student = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='activity_absences'
    )

    seance_number = models.PositiveIntegerField(
        help_text="Numéro de la séance (1 → N)"
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('activity', 'student', 'seance_number')
        ordering = ['seance_number']

    def __str__(self):
        return f"{self.student} absent | {self.activity} | séance {self.seance_number}"

class Exam(models.Model):
    SEMESTER = (
        ('s1', 'الفصل الأول'),
        ('s2', 'الفصل الثاني'),
        ('s3', 'الفصل الثالث'),
        ('s4', 'الفصل الرابع'),
    )
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='exams')
    num_count = models.PositiveIntegerField(null=True, blank=True)
    num_hivd = models.PositiveIntegerField(null=True, blank=True)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, related_name='ac_exams', default=get_default_academic_year )

    tjwid = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    moyen = models.DecimalField(max_digits=5, decimal_places=2, null=True,  blank=True)
    houdour = models.DecimalField(max_digits=5, decimal_places=2, null=True,  blank=True)
    NB = models.CharField(max_length=255, null=True, blank=True )
    date = models.DateField(null=True, blank=True)
    semester = models.CharField(max_length=150, choices=SEMESTER)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Exam {self.id} - {self.student}"

class AbsElmhdara(models.Model):
    MONTH = (
        (1, 'يناير'),
        (2, 'فبراير'),
        (3, 'مارس'),
        (4, 'أبريل'),
        (5, 'مايو'),
        (6, 'يونيو'),
        (7, 'يوليو'),
        (8, 'أغسطس'),
        (9, 'سبتمبر'),
        (10, 'أكتوبر'),
        (11, 'نوفمبر'),
        (12, 'ديسمبر')
    )
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='abs_elmhdara')
    num_ab_ac = models.PositiveIntegerField(null=True, blank=True)
    num_ab_no = models.PositiveIntegerField(null=True, blank=True)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, related_name='ac_abs_els', default=get_default_academic_year )

    NB = models.CharField(max_length=255, null=True, blank=True )
    date = models.DateField(null=True, blank=True)
    month = models.CharField(max_length=150, choices=MONTH)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Exam {self.id} - {self.student}"

class Competition(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    start_date = models.DateField()
    end_date = models.DateField()
    number_of_tasfiyat = models.PositiveIntegerField(default=1) 
    is_active = models.BooleanField(default=True)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='competitions',
        default=get_default_academic_year
    )

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.title

class Tasfiya(models.Model):
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='tasfiyat'
    )
    name = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ('competition', 'order')

    def __str__(self):
        return f"{self.competition.title} - {self.name}"

class Juge(models.Model):
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='juges'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judge_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('competition', 'user')

    def __str__(self):
        return f"{self.user} - {self.competition}"

class CompetitionLevel(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competition_participation'
    )

class Participant(models.Model):

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='competition_participations'
    )
    level = models.ForeignKey(
        CompetitionLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competition_level_participations'
    )

    class Meta:
        unique_together = ('competition', 'etudiant')

    def __str__(self):
        return f"{self.etudiant}"

class Evaluation(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    juge = models.ForeignKey(
        Juge,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    tasfiya = models.ForeignKey(
        Tasfiya,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )

    personality = models.DecimalField(max_digits=6, decimal_places=2)
    voice = models.DecimalField(max_digits=6, decimal_places=2)
    performance = models.DecimalField(max_digits=6, decimal_places=2)
    memorization = models.DecimalField(max_digits=6, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('participant', 'juge', 'tasfiya')
        ordering = ['id']


    def total_score(self):
        return (
            self.personality +
            self.voice +
            self.performance +
            self.memorization
        )

    def __str__(self):
        return f"{self.participant} - {self.juge}"

class EtudiantCertified(models.Model):

    TYPE_IJAZA_CHOICES = [
        ('حافظ', 'حافظ'),
        ('مجازي', 'مجازي'),
    ]

    TYPE_CHOICES = [
        ('نافع', 'نافع'),
        ('حفص', 'حفص'),
        ('أخر', 'أخر'),
    ]

    full_name = models.CharField(max_length=255)
    NNI = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)

    date = models.DateField()
    birth_date = models.DateField()

    birth_city = models.CharField(max_length=255)

    photo = models.ImageField(upload_to=upload_student_photo, null=True, blank=True)

    year = models.PositiveIntegerField()

    type_ijaza = models.CharField(
        max_length=20,
        choices=TYPE_IJAZA_CHOICES
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    def __str__(self):
        return self.full_name

class Attestation(models.Model):
    TYPE_CHOICES = [
        ('certificat', 'إفادة'),
        ('felicitation', 'تهنئة'),
        ('condolence', 'تعزية'),
    ]

    etudiant = models.ForeignKey(
        'Etudiant',
        on_delete=models.CASCADE,
        blank=True, null=True, 
        related_name='attestations'
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    deceased = models.CharField(max_length=255, blank=True, null=True)
    elmouaza = models.CharField(max_length=255, blank=True, null=True)
    mention = models.CharField(max_length=255, blank=True, null=True)

    date_emission = models.DateField(default=timezone.now)

    # Optional fields
    mention = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.etudiant.student_name} - {self.type}"

