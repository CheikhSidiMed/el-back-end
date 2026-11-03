from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0104_add_fee_comparison_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlyreport',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
