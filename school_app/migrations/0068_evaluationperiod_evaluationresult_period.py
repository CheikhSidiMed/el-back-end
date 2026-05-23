from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0067_evaluationresult_user'),
    ]

    operations = [
        # 1. Create EvaluationPeriod table
        migrations.CreateModel(
            name='EvaluationPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('academic_year', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='evaluation_periods',
                    to='school_app.academicyear',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # 2. Make month and year nullable on EvaluationResult
        migrations.AlterField(
            model_name='evaluationresult',
            name='month',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='evaluationresult',
            name='year',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),

        # 3. Add period FK to EvaluationResult
        migrations.AddField(
            model_name='evaluationresult',
            name='period',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='results',
                to='school_app.evaluationperiod',
            ),
        ),

        # 4. Drop old unique_together on (student, month, year)
        migrations.AlterUniqueTogether(
            name='evaluationresult',
            unique_together=set(),
        ),

        # 5. Add new unique_together on (student, period)
        migrations.AlterUniqueTogether(
            name='evaluationresult',
            unique_together={('student', 'period')},
        ),
    ]
