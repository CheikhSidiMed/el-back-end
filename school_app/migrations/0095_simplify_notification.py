import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0094_school_notification'),
    ]

    operations = [
        migrations.RemoveField(model_name='schoolnotification', name='notification_type'),
        migrations.RemoveField(model_name='schoolnotification', name='scheduled_month'),
        migrations.RemoveField(model_name='schoolnotification', name='scheduled_year'),
        migrations.AlterField(
            model_name='schoolnotification',
            name='scheduled_date',
            field=models.DateField(default=datetime.date.today),
            preserve_default=False,
        ),
    ]
