"""API for the task management feature (إدارة المهام).

tasks/                       managers (fTasks): all tasks, CRUD; others: own tasks, read-only
tasks/my/                    current user's tasks
tasks/{id}/progress/         PATCH status/progress by the assignee
tasks/stats/                 managers: totals + per-user breakdown
task-notifications/          current user's inbox (also generates due reminders)
task-notifications/{id}/read/, task-notifications/read-all/
"""
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Job, Task, TaskNotification
from .task_reminders import DEADLINE_KINDS, clear_task_reminders, notify_assigned, sync_task_reminders
from .task_serializers import TaskNotificationSerializer, TaskProgressSerializer, TaskSerializer

MANAGE_TASKS_PERMISSION = 'fTasks'


def user_has_permission(user, code):
    """True if the user's main role or one of their extra roles grants `code`."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or (user.role_id and user.role.title == 'admin_g'):
        return True
    return Job.objects.filter(
        Q(utilisateur=user) | Q(extra_users=user), permissions__code=code
    ).exists()


def overdue_q(now=None):
    return Q(status__in=Task.OPEN_STATUSES, due_date__lt=now or timezone.now())


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = []  # filtered by hand: supports the virtual "overdue" status

    def _is_manager(self):
        if not hasattr(self, '_manager_cache'):
            self._manager_cache = user_has_permission(self.request.user, MANAGE_TASKS_PERMISSION)
        return self._manager_cache

    def _require_manager(self):
        if not self._is_manager():
            raise PermissionDenied('ليست لديك صلاحية إدارة المهام')

    def get_queryset(self):
        qs = Task.objects.select_related('assigned_to', 'created_by')
        if self.action in ('my', 'progress') or not self._is_manager():
            qs = qs.filter(assigned_to=self.request.user)
        return qs

    def filter_queryset(self, qs):
        if self.action != 'list':
            return qs
        p = self.request.query_params
        if p.get('assigned_to'):
            qs = qs.filter(assigned_to_id=p['assigned_to'])
        if p.get('priority'):
            qs = qs.filter(priority=p['priority'])
        if p.get('search'):
            qs = qs.filter(Q(title__icontains=p['search']) | Q(description__icontains=p['search']))
        st = p.get('status')
        if st == 'overdue':
            qs = qs.filter(overdue_q())
        elif st in Task.OPEN_STATUSES:
            qs = qs.filter(status=st).exclude(overdue_q())
        elif st:
            qs = qs.filter(status=st)
        return qs

    def create(self, request, *args, **kwargs):
        self._require_manager()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._require_manager()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._require_manager()
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user, assigned_at=timezone.now())
        notify_assigned(task)

    def perform_update(self, serializer):
        old_assignee = serializer.instance.assigned_to_id
        old_due = serializer.instance.due_date
        new_assignee = serializer.validated_data.get('assigned_to')
        reassigned = new_assignee is not None and new_assignee.pk != old_assignee
        extra = {'assigned_at': timezone.now()} if reassigned else {}
        task = serializer.save(**extra)
        if reassigned or task.due_date != old_due:
            clear_task_reminders(task)
        if reassigned:
            notify_assigned(task)

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    @action(detail=True, methods=['patch'], url_path='progress')
    def progress(self, request, pk=None):
        task = self.get_object()
        serializer = TaskProgressSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskSerializer(task).data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        self._require_manager()
        late = overdue_q()
        counts = dict(
            total=Count('id'),
            new=Count('id', filter=Q(status=Task.STATUS_NEW) & ~late),
            in_progress=Count('id', filter=Q(status=Task.STATUS_IN_PROGRESS) & ~late),
            completed=Count('id', filter=Q(status=Task.STATUS_COMPLETED)),
            cancelled=Count('id', filter=Q(status=Task.STATUS_CANCELLED)),
            overdue=Count('id', filter=late),
        )

        # «نسبة الإنجاز» = average progress of non-cancelled tasks (a completed task counts as 100%).
        counts['avg_progress'] = Avg('progress', filter=~Q(status=Task.STATUS_CANCELLED))

        def completion_rate(row):
            return round(row.pop('avg_progress') or 0)

        totals = Task.objects.aggregate(**counts)
        totals['completion_rate'] = completion_rate(totals)
        rows = (Task.objects
                .values('assigned_to', 'assigned_to__first_name', 'assigned_to__phone')
                .annotate(**counts)
                .order_by('-total'))
        totals['by_user'] = [
            {
                'user_id': row['assigned_to'],
                'name': row['assigned_to__first_name'] or row['assigned_to__phone'],
                'completion_rate': completion_rate(row),
                **{key: row[key] for key in counts if key != 'avg_progress'},
            }
            for row in rows
        ]
        return Response(totals)


class TaskNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskNotificationSerializer
    filter_backends = []

    def get_queryset(self):
        return (TaskNotification.objects
                .filter(user=self.request.user)
                .exclude(task__status=Task.STATUS_CANCELLED)
                .exclude(task__status=Task.STATUS_COMPLETED, kind__in=DEADLINE_KINDS)
                .select_related('task'))

    def list(self, request, *args, **kwargs):
        sync_task_reminders(request.user)
        qs = self.get_queryset()
        my_tasks = Task.objects.filter(assigned_to=request.user)
        return Response({
            'results': self.get_serializer(qs[:30], many=True).data,
            'unread_count': qs.filter(is_read=False).count(),
            'overdue_count': my_tasks.filter(overdue_q()).count(),
            'open_count': my_tasks.filter(status__in=Task.OPEN_STATUSES).count(),
        })

    @action(detail=True, methods=['post'], url_path='read')
    def read(self, request, pk=None):
        self.get_queryset().filter(pk=pk).update(is_read=True)
        return Response({'detail': 'ok'})

    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': 'ok'})
