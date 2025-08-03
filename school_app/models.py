from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager

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
    ROLES = (
        ('admin_g', 'المدير العام'),
        ('admin', 'مدير التسجيل والحسابات'),
        ('dg_lessen', 'مدير الدروس'),
        ('admin_m', 'إدارة المقرأة'),
        ('teacher', 'أستاذ(ة)'),
        ('user', 'المراقب'),
    )

    role = models.CharField(max_length=20, choices=ROLES, default='user')

    username = None
    last_name = None
    email = None

    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UtilisateurManager()

    def __str__(self):
        return self.phone or "Utilisateur sans numéro"

class Branche(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.TextField()

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Branche"
        verbose_name_plural = "Branches"

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
    gender = models.CharField(max_length=1, choices=[('M', 'ذكر'), ('F', 'أنثى')])
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=100, null=True, blank=True)
    date_inscription = models.DateField(auto_now_add=True)
    student_photo = models.ImageField(upload_to='etudiants_photos/', null=True, blank=True)

    payment_nature = models.CharField(
        max_length=20,
        choices=[('free', 'Gratuit'), ('mensuel', 'Mensuel')],
        default='mensuel'
    )

    fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    remaining = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    classe = models.ForeignKey('Classe', on_delete=models.CASCADE)
    branche = models.ForeignKey('Branche', on_delete=models.CASCADE)
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

class Paiement(models.Model):
    date_paiement = models.DateField(auto_now_add=True)
    montant_paye = models.DecimalField(max_digits=8, decimal_places=2)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    mois = models.ForeignKey(Mois, on_delete=models.CASCADE)
    methode_paiement = models.CharField(max_length=50)
    reference_transaction = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.etudiant.student_name} - {self.montant_paye} MRU - {self.mois}"

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
        unique_together = ['student', 'date', 'session']  # no duplicate absence per session

    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.get_session_display()})"
