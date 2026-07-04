from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0076_delivery_receipt_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='etudiant',
            name='is_residence',
            field=models.BooleanField(default=False),
        ),
    ]
