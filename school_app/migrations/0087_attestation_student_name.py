from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0086_agent_last_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='attestation',
            name='student_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
