"""Per-user task notifications, computed on demand (no scheduler needed).

The frontend polls `task-notifications/` every minute; `sync_task_reminders` runs at the
start of that call and creates any due_soon / due_now reminder that has become relevant.
"""
from datetime import timedelta

from django.utils import timezone

from .models import Task, TaskNotification

DUE_SOON_WINDOW = timedelta(hours=24)
DEADLINE_KINDS = ('due_soon', 'due_now')


def notify_assigned(task):
    """(Re)create the `assigned` notification for the task's current assignee."""
    TaskNotification.objects.update_or_create(
        user=task.assigned_to, task=task, kind='assigned',
        defaults={'is_read': False, 'created_at': timezone.now()},
    )


def clear_task_reminders(task):
    """Drop deadline reminders (and stale notifications of a previous assignee)."""
    task.notifications.filter(kind__in=DEADLINE_KINDS).delete()
    task.notifications.exclude(user=task.assigned_to).delete()


def sync_task_reminders(user):
    now = timezone.now()
    open_tasks = Task.objects.filter(assigned_to=user, status__in=Task.OPEN_STATUSES,
                                     due_date__lte=now + DUE_SOON_WINDOW)
    for task in open_tasks:
        kind = 'due_now' if task.due_date <= now else 'due_soon'
        TaskNotification.objects.get_or_create(user=user, task=task, kind=kind)
