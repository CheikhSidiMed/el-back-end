from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0101_etudiant_free_reason'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['bank_id', 'date'], name='tx_bank_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account_id', 'date'], name='tx_account_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['employee_id', 'date'], name='tx_employee_date_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['bank_id', 'type'], name='tx_bank_type_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account_id', 'type'], name='tx_account_type_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['date'], name='tx_date_idx'),
        ),
    ]
