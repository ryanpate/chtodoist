"""
Database models for chtodoist task management
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TaskTemplate(models.Model):
    """
    Templates for recurring tasks with dynamic naming
    Allows custom task names with variable substitution (e.g., dates)
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=255, help_text="Template name (for reference)")
    content_template = models.CharField(
        max_length=500,
        help_text="Task content with placeholders. Example: 'Weekly Report - {date}'"
    )
    description_template = models.TextField(
        blank=True,
        help_text="Task description template (optional)"
    )
    project_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Todoist project ID (leave blank for Inbox)"
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='weekly'
    )
    priority = models.IntegerField(
        default=1,
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Urgent')],
        help_text="Task priority (1-4)"
    )
    labels = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated label names"
    )
    auto_complete = models.BooleanField(
        default=False,
        help_text="Auto-complete this task after due date"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether to generate new tasks from this template"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When was the last task generated from this template"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task Template'
        verbose_name_plural = 'Task Templates'

    def __str__(self):
        return f"{self.name} ({self.frequency})"

    def get_labels_list(self):
        """Return labels as a list"""
        if self.labels:
            return [label.strip() for label in self.labels.split(',')]
        return []


class AutoCompleteRule(models.Model):
    """
    Rules for automatically completing tasks after their due date
    """
    todoist_task_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Todoist task ID to auto-complete"
    )
    task_content = models.CharField(
        max_length=500,
        help_text="Task name (for reference)"
    )
    complete_after_hours = models.IntegerField(
        default=0,
        help_text="Hours after due date to auto-complete (0 = immediately when overdue)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rule is active"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='autocomplete_rules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task was auto-completed"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Auto-Complete Rule'
        verbose_name_plural = 'Auto-Complete Rules'

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.task_content} - {status}"


class TaskWatcher(models.Model):
    """
    Multi-user assignments - track additional users watching a task
    (Todoist only supports one assignee, so we track watchers separately)
    """
    todoist_task_id = models.CharField(
        max_length=50,
        help_text="Todoist task ID"
    )
    task_content = models.CharField(
        max_length=500,
        help_text="Task name (cached for display)"
    )
    watcher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='watched_tasks',
        help_text="User watching this task"
    )
    added_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='watchers_added',
        help_text="User who added this watcher"
    )
    added_at = models.DateTimeField(auto_now_add=True)
    notify_on_update = models.BooleanField(
        default=True,
        help_text="Notify watcher when task is updated"
    )
    notify_on_complete = models.BooleanField(
        default=True,
        help_text="Notify watcher when task is completed"
    )
    notify_on_overdue = models.BooleanField(
        default=True,
        help_text="Notify watcher when task becomes overdue"
    )

    class Meta:
        ordering = ['-added_at']
        unique_together = ['todoist_task_id', 'watcher']
        verbose_name = 'Task Watcher'
        verbose_name_plural = 'Task Watchers'

    def __str__(self):
        return f"{self.watcher.username} watching: {self.task_content}"


class Notification(models.Model):
    """
    In-app notifications for users
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_updated', 'Task Updated'),
        ('task_completed', 'Task Completed'),
        ('task_overdue', 'Task Overdue'),
        ('watcher_added', 'Added as Watcher'),
        ('comment_added', 'Comment Added'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    todoist_task_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Related Todoist task ID (if applicable)"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.user.username} - {self.title} ({status})"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class GeneratedTask(models.Model):
    """
    Track tasks generated from templates to avoid duplicates
    """
    template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='generated_tasks'
    )
    todoist_task_id = models.CharField(
        max_length=50,
        help_text="ID of the generated Todoist task"
    )
    task_content = models.CharField(max_length=500)
    due_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-due_date']
        verbose_name = 'Generated Task'
        verbose_name_plural = 'Generated Tasks'

    def __str__(self):
        return f"{self.task_content} (from {self.template.name})"
