from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0097_add_schedule_library_notification_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyabsence',
            name='agent_response',
            field=models.TextField(blank=True, null=True),
        ),
    ]
