from django.db import migrations


def add_permissions(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')

    fData = Permission.objects.filter(code='fData').first()

    Permission.objects.get_or_create(
        code='fFeeComparison',
        defaults={'label': 'مقارنة الرسوم', 'parent': fData},
    )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')
    Permission.objects.filter(code='fFeeComparison').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0103_fix_october_academic_year'),
    ]

    operations = [
        migrations.RunPython(add_permissions, remove_permissions),
    ]
