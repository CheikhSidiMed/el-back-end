from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0105_monthlyreport_is_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='quarterlyreport',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='evaluationresult',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='evaluationmonthresult',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tehejireport',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
