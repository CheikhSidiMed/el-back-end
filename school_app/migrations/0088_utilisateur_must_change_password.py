from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0087_attestation_student_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilisateur',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
    ]
