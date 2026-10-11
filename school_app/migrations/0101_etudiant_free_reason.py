from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0100_utilisateur_extra_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='etudiant',
            name='free_reason',
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name='سبب الإعفاء',
            ),
        ),
    ]
