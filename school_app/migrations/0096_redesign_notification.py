from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0095_simplify_notification'),
    ]

    operations = [
        migrations.RemoveField(model_name='schoolnotification', name='scheduled_date'),
        migrations.AddField(
            model_name='schoolnotification',
            name='notification_type',
            field=models.CharField(
                choices=[('instant', 'فوري'), ('monthly_day', 'يوم شهري')],
                default='instant',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='schoolnotification',
            name='day_of_month',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
