import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0071_etudiantcertified_ijazat'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExitCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.TextField(blank=True, null=True, verbose_name='الحالة العامة للمحفوظات')),
                ('level', models.CharField(blank=True, max_length=200, null=True, verbose_name='المستوى')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='الملحوظات')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='التاريخ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='exit_certificates',
                    to='school_app.etudiant',
                    verbose_name='الطالب',
                )),
            ],
            options={
                'verbose_name': 'إفادة تحديد مستوى',
                'ordering': ['-created_at'],
            },
        ),
    ]
