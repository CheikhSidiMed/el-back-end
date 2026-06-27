from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0073_evaluationmonthresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilisateur',
            name='agent_profile',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='user_account',
                to='school_app.agent',
            ),
        ),
    ]
