from django.contrib import admin

# Register your models here.
from .models import (
    Branche, Classe, Niveau, Agent, Receipt, SalaryPayment,
    ReceiptPayment, Job, Inscription, Garant, GarantPaiement,
    Employee, Transaction, Etudiant, Mois, Paiement,
    BankAccount, Utilisateur, Activity, AcademicYear,
    MonthlyReport, DailyAbsence, AccountCategory, Account,
    Permission, Suspension, AbsenceActivity
)

admin.site.register(Branche)
admin.site.register(Classe)
admin.site.register(Niveau)
admin.site.register(Agent)
admin.site.register(Receipt)
admin.site.register(SalaryPayment)
admin.site.register(ReceiptPayment)
admin.site.register(Job)
admin.site.register(Inscription)
admin.site.register(Garant)
admin.site.register(GarantPaiement)
admin.site.register(Employee)
admin.site.register(Transaction)
admin.site.register(Etudiant)
admin.site.register(Mois)
admin.site.register(Paiement)
admin.site.register(BankAccount)
admin.site.register(Utilisateur)
admin.site.register(Activity)
admin.site.register(AcademicYear)
admin.site.register(MonthlyReport)
admin.site.register(DailyAbsence)
admin.site.register(AccountCategory)
admin.site.register(Account)
admin.site.register(Permission)
admin.site.register(Suspension)
admin.site.register(AbsenceActivity)
