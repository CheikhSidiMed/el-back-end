from django.db import migrations


def fix_october_payments(apps, schema_editor):
    """
    Move October 2026 payments from academic year 2025-2026 → 2026-2027.
    Applies to: Paiement, GarantPaiement, SalaryPayment, PaiementTransations.
    """
    AcademicYear        = apps.get_model('school_app', 'AcademicYear')
    Paiement            = apps.get_model('school_app', 'Paiement')
    GarantPaiement      = apps.get_model('school_app', 'GarantPaiement')
    SalaryPayment       = apps.get_model('school_app', 'SalaryPayment')
    PaiementTransations = apps.get_model('school_app', 'PaiementTransations')

    try:
        old_year = AcademicYear.objects.get(year='2025-2026')
    except AcademicYear.DoesNotExist:
        return  # nothing to do

    try:
        new_year = AcademicYear.objects.get(year='2026-2027')
    except AcademicYear.DoesNotExist:
        return  # target year doesn't exist yet

    # Paiement: payment_date in October 2026, month=10, old year
    count = Paiement.objects.filter(
        academic_year=old_year,
        month=10,
        payment_date__year=2026,
        payment_date__month=10,
    ).update(academic_year=new_year)
    print(f"  Paiement: {count} records moved")

    # GarantPaiement: payment_date in October 2026, month=10, old year
    count = GarantPaiement.objects.filter(
        academic_year=old_year,
        month=10,
        payment_date__year=2026,
        payment_date__month=10,
    ).update(academic_year=new_year)
    print(f"  GarantPaiement: {count} records moved")

    # SalaryPayment: month=10 (October), old year
    count = SalaryPayment.objects.filter(
        academic_year=old_year,
        month=10,
    ).update(academic_year=new_year)
    print(f"  SalaryPayment: {count} records moved")

    # PaiementTransations: payment_date in October 2026, month=10, old year
    count = PaiementTransations.objects.filter(
        academic_year=old_year,
        month=10,
        payment_date__year=2026,
        payment_date__month=10,
    ).update(academic_year=new_year)
    print(f"  PaiementTransations: {count} records moved")


def reverse_fix(apps, schema_editor):
    AcademicYear        = apps.get_model('school_app', 'AcademicYear')
    Paiement            = apps.get_model('school_app', 'Paiement')
    GarantPaiement      = apps.get_model('school_app', 'GarantPaiement')
    SalaryPayment       = apps.get_model('school_app', 'SalaryPayment')
    PaiementTransations = apps.get_model('school_app', 'PaiementTransations')

    try:
        old_year = AcademicYear.objects.get(year='2025-2026')
        new_year = AcademicYear.objects.get(year='2026-2027')
    except AcademicYear.DoesNotExist:
        return

    Paiement.objects.filter(academic_year=new_year, month=10).update(academic_year=old_year)
    GarantPaiement.objects.filter(academic_year=new_year, month=10).update(academic_year=old_year)
    SalaryPayment.objects.filter(academic_year=new_year, month=10).update(academic_year=old_year)
    PaiementTransations.objects.filter(academic_year=new_year, month=10).update(academic_year=old_year)


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0102_transaction_indexes'),
    ]

    operations = [
        migrations.RunPython(fix_october_payments, reverse_code=reverse_fix),
    ]
