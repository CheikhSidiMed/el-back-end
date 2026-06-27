from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0072_exitcertificate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationMonthResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('louh', models.CharField(blank=True, max_length=100, null=True)),
                ('ahzab', models.CharField(blank=True, max_length=100, null=True)),
                ('adaa', models.CharField(blank=True, max_length=100, null=True)),
                ('taqdir', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='month_results', to='school_app.evaluationperiod')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='month_results', to='school_app.etudiant')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='month_results', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('student', 'period')},
            },
        ),
    ]
