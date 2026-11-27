from django.db import migrations

CODE = 'fTasks'
MANAGER_ROLES = ['admin_g', 'admin']


def add_permission(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')
    Job = apps.get_model('school_app', 'Job')

    perm, _ = Permission.objects.get_or_create(code=CODE, defaults={'label': 'إدارة المهام', 'parent': None})
    for job in Job.objects.filter(title__in=MANAGER_ROLES):
        job.permissions.add(perm)


def remove_permission(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')
    Permission.objects.filter(code=CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0109_task_tasknotification'),
    ]

    operations = [
        migrations.RunPython(add_permission, remove_permission),
    ]
