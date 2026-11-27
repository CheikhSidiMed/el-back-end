"""Serializers for the task management feature (إدارة المهام)."""
from django.utils import timezone
from rest_framework import serializers

from .models import Task, TaskNotification


def apply_task_status_rules(attrs, instance=None):
    """completed → progress 100 + completed_at; leaving completed clears completed_at."""
    status_value = attrs.get('status', getattr(instance, 'status', None))
    if status_value == Task.STATUS_COMPLETED:
        attrs['progress'] = 100
        already_completed = instance and instance.status == Task.STATUS_COMPLETED and instance.completed_at
        if not already_completed:
            attrs['completed_at'] = timezone.now()
    elif 'status' in attrs:
        attrs['completed_at'] = None
        reopened_to_new = attrs['status'] == Task.STATUS_NEW and 'progress' not in attrs
        if reopened_to_new and instance and instance.progress == 100:
            attrs['progress'] = 0
    return attrs


class TaskSerializer(serializers.ModelSerializer):
    effective_status = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_to', 'assigned_to_name',
            'created_by', 'created_by_name', 'start_date', 'due_date', 'assigned_at',
            'duration_preset', 'priority', 'status', 'effective_status', 'is_overdue',
            'progress', 'completed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'assigned_at', 'completed_at', 'created_at', 'updated_at']

    def get_effective_status(self, obj):
        return 'overdue' if obj.is_overdue else obj.status

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to_id else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by_id else None

    def validate_progress(self, value):
        if value > 100:
            raise serializers.ValidationError('نسبة الإنجاز يجب أن تكون بين 0 و 100')
        return value

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        due = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        if start and due and due <= start:
            raise serializers.ValidationError({'due_date': 'تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية'})
        return apply_task_status_rules(attrs, self.instance)


class TaskProgressSerializer(serializers.ModelSerializer):
    """The only fields the assignee may change on their own task."""
    status = serializers.ChoiceField(
        choices=[Task.STATUS_NEW, Task.STATUS_IN_PROGRESS, Task.STATUS_COMPLETED], required=False
    )
    progress = serializers.IntegerField(min_value=0, max_value=100, required=False)

    class Meta:
        model = Task
        fields = ['status', 'progress']

    def validate(self, attrs):
        if self.instance.status == Task.STATUS_CANCELLED:
            raise serializers.ValidationError('لا يمكن تعديل مهمة ملغاة')
        # Moving the progress slider on a "new" task means work has started.
        if attrs.get('progress') and 'status' not in attrs and self.instance.status == Task.STATUS_NEW:
            attrs['status'] = Task.STATUS_IN_PROGRESS
        return apply_task_status_rules(attrs, self.instance)


class TaskNotificationSerializer(serializers.ModelSerializer):
    task = serializers.SerializerMethodField()

    class Meta:
        model = TaskNotification
        fields = ['id', 'kind', 'is_read', 'created_at', 'task']

    def get_task(self, obj):
        t = obj.task
        return {'id': t.id, 'title': t.title, 'due_date': t.due_date, 'priority': t.priority}
