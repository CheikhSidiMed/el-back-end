from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0099_agent_phone_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilisateur',
            name='extra_roles',
            field=models.ManyToManyField(
                blank=True,
                related_name='extra_users',
                to='school_app.job',
            ),
        ),
    ]
