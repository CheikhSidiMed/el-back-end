from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0088_utilisateur_must_change_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='transfer_ref',
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True),
        ),
    ]
