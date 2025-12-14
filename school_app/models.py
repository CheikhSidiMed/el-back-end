from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import date

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
        ('admin_g', 'المدير العام'),
        ('admin', 'مدير التسجيل والحسابات'),
        ('dg_lessen', 'مدير الدروس'),
        ('admin_m', 'إدارة المقرأة'),
        ('teacher', 'أستاذ(ة)'),
        ('user', 'المراقب'),
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
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    username = None
    last_name = None
    email = None

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UtilisateurManager()

    def __str__(self):
        return self.phone or "Utilisateur sans numéro"

class Classe(models.Model):
    nom = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50, null=True, blank=True)
    branche = models.ForeignKey(Branche, on_delete=models.CASCADE, related_name='classes',
    null=True, blank=True )

    def __str__(self):
        return f"{self.nom} - {self.niveau}"

class Niveau(models.Model):
    level_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.level_name

class Agent(models.Model):
    agent_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    phone_2 = models.CharField(max_length=20, null=True, blank=True)
    profession = models.CharField(max_length=100, null=True, blank=True)
    whatsapp_phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.agent_name

class Etudiant(models.Model):
    student_name = models.CharField(max_length=100)
    part_count = models.PositiveIntegerField(default=1)
    is_inscrire = models.PositiveIntegerField(default=1)  # 1 = inscrit, 0 = not inscrit
    gender = models.CharField(max_length=1, choices=[('M', 'ذكر'), ('F', 'أنثى')])
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=100, null=True, blank=True)
    date_inscription = models.DateField(default=date.today)
    date_count = models.DateField(auto_now_add=True)
    student_photo = models.ImageField(upload_to='etudiants_photos/', null=True, blank=True)

    payment_nature = models.CharField(
        max_length=20,
        choices=[('free', 'Gratuit'), ('mensuel', 'Mensuel')],
        default='mensuel'
    )

    fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    remaining = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    classe = models.ForeignKey('Classe', null=True, blank=True, on_delete=models.CASCADE)
    branche = models.ForeignKey('Branche', null=True, blank=True, on_delete=models.CASCADE)
    agent = models.ForeignKey('Agent', null=True, blank=True, on_delete=models.SET_NULL)

    phone = models.CharField(max_length=20, null=True, blank=True)
    level = models.ForeignKey('Niveau', null=True, blank=True, on_delete=models.SET_NULL)

    rewaya = models.CharField(max_length=50, null=True, blank=True)
    days = models.CharField(max_length=100, null=True, blank=True)
    tdate = models.DateField(null=True, blank=True)
    start = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    elmoutoune = models.CharField(max_length=20, null=True, blank=True)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    date_desectivation = models.DateField(null=True, blank=True)
    suspension_reason = models.TextField(null=True, blank=True)

    current_city = models.CharField(max_length=100, null=True, blank=True)
    etat = models.CharField(
        max_length=50,
        choices=[('inscrit', 'Inscrit'), ('suspendu', 'Suspendu')],
        default='inscrit'
    )

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

    def __str__(self):
        return f"{self.name} ({self.session})"

class AcademicYear(models.Model):
    year        = models.CharField(max_length=9, unique=True, help_text="ex: 2024-2025")
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
    month = models.CharField(max_length=20)  # or use IntegerField for 1–12 if preferred

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

class Employee(models.Model):
    number = models.CharField(max_length=50, unique=True)  # matricule ou code employé
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
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    subscription_date = models.DateField()
    is_actif = models.BooleanField(default=True) 
    id_number = models.CharField(max_length=100, blank=True, null=True)

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
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=13, decimal_places=2, default=0)

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

    def __str__(self):
        return f"{self.name} ({self.category})"

class Inscription(models.Model):
    """Join table with extra fields for a student's registration to an activity"""
    student = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
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
    date_c = models.DateField(default=timezone.now)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

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
    date = models.DateTimeField(default=timezone.now)

    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='plus')

    bank = models.ForeignKey(
        'BankAccount',
        on_delete=models.PROTECT,
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

