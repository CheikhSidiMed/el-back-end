from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0085_student_class_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='agent',
            name='last_reminder_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
