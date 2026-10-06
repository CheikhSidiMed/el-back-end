from django.db import migrations


def add_permissions(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')

    fData = Permission.objects.filter(code='fData').first()

    new_perms = [
        ('fSchedule',      'الجدول الدراسي',       fData),
        ('fLibrary',       'المكتبة الإلكترونية',   fData),
        ('fNotifications', 'الإشعارات',             fData),
    ]

    for code, label, parent in new_perms:
        Permission.objects.get_or_create(
            code=code,
            defaults={'label': label, 'parent': parent},
        )


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')
    Permission.objects.filter(code__in=['fSchedule', 'fLibrary', 'fNotifications']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0096_redesign_notification'),
    ]

    operations = [
        migrations.RunPython(add_permissions, remove_permissions),
    ]
