"""Permissions for the task management feature, grouped like the other menu sections:

    fTasksGestion  «المهام»          (parent / sidebar group)
      ├─ fMyTasks  «مهامي»           → every staff role (all roles except agent)
      └─ fTasks    «إدارة المهام»    → admin_g, admin (created in 0110, moved under the group)
"""
from django.db import migrations

PARENT = ('fTasksGestion', 'المهام')
MY_TASKS = ('fMyTasks', 'مهامي')
MANAGE = ('fTasks', 'إدارة المهام')
NON_STAFF_ROLES = ['agent']
MANAGER_ROLES = ['admin_g', 'admin']


def add_permissions(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')
    Job = apps.get_model('school_app', 'Job')

    parent, _ = Permission.objects.get_or_create(code=PARENT[0], defaults={'label': PARENT[1], 'parent': None})
    my_tasks, _ = Permission.objects.get_or_create(code=MY_TASKS[0], defaults={'label': MY_TASKS[1], 'parent': parent})
    manage, _ = Permission.objects.get_or_create(code=MANAGE[0], defaults={'label': MANAGE[1], 'parent': parent})

    # fTasks was created as a root permission in 0110 → move it under the group.
    for perm in (my_tasks, manage):
        if perm.parent_id != parent.id:
            perm.parent = parent
            perm.save(update_fields=['parent'])

    # Every staff role sees the group and «مهامي».
    for job in Job.objects.exclude(title__in=NON_STAFF_ROLES):
        job.permissions.add(parent, my_tasks)

    # Managers keep «إدارة المهام».
    for job in Job.objects.filter(title__in=MANAGER_ROLES):
        job.permissions.add(manage)


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model('school_app', 'Permission')
    # Put fTasks back at the root (state after 0110), then drop the new ones.
    Permission.objects.filter(code=MANAGE[0]).update(parent=None)
    Permission.objects.filter(code__in=[MY_TASKS[0], PARENT[0]]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0110_add_tasks_permission'),
    ]

    operations = [
        migrations.RunPython(add_permissions, remove_permissions),
    ]
