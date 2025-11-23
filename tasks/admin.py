"""
Django admin configuration for chtodoist models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TaskTemplate,
    AutoCompleteRule,
    TaskWatcher,
    Notification,
    GeneratedTask
)


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'frequency',
        'priority',
        'is_active',
        'auto_complete',
        'created_by',
        'last_generated'
    ]
    list_filter = ['frequency', 'priority', 'is_active', 'auto_complete', 'created_at']
    search_fields = ['name', 'content_template', 'description_template']
    readonly_fields = ['created_at', 'updated_at', 'last_generated']
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'content_template', 'description_template')
        }),
        ('Task Settings', {
            'fields': ('project_id', 'frequency', 'priority', 'labels')
        }),
        ('Options', {
            'fields': ('auto_complete', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_generated'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AutoCompleteRule)
class AutoCompleteRuleAdmin(admin.ModelAdmin):
    list_display = [
        'task_content',
        'todoist_task_id',
        'complete_after_hours',
        'is_active',
        'created_by',
        'status_badge'
    ]
    list_filter = ['is_active', 'created_at', 'completed_at']
    search_fields = ['task_content', 'todoist_task_id']
    readonly_fields = ['created_at', 'completed_at']
    fieldsets = (
        ('Task Information', {
            'fields': ('todoist_task_id', 'task_content')
        }),
        ('Auto-Complete Settings', {
            'fields': ('complete_after_hours', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        if obj.completed_at:
            return format_html(
                '<span style="color: green;">✓ Completed</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="color: blue;">⚡ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">○ Inactive</span>'
            )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskWatcher)
class TaskWatcherAdmin(admin.ModelAdmin):
    list_display = [
        'task_content_short',
        'todoist_task_id',
        'watcher',
        'added_by',
        'added_at',
        'notification_status'
    ]
    list_filter = [
        'notify_on_update',
        'notify_on_complete',
        'notify_on_overdue',
        'added_at'
    ]
    search_fields = ['task_content', 'todoist_task_id', 'watcher__username']
    readonly_fields = ['added_at']
    fieldsets = (
        ('Task Information', {
            'fields': ('todoist_task_id', 'task_content')
        }),
        ('Watcher', {
            'fields': ('watcher', 'added_by')
        }),
        ('Notification Settings', {
            'fields': ('notify_on_update', 'notify_on_complete', 'notify_on_overdue')
        }),
        ('Metadata', {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )

    def task_content_short(self, obj):
        if len(obj.task_content) > 50:
            return obj.task_content[:50] + '...'
        return obj.task_content
    task_content_short.short_description = 'Task'

    def notification_status(self, obj):
        notifications = []
        if obj.notify_on_update:
            notifications.append('Update')
        if obj.notify_on_complete:
            notifications.append('Complete')
        if obj.notify_on_overdue:
            notifications.append('Overdue')
        return ', '.join(notifications) if notifications else 'None'
    notification_status.short_description = 'Notifications'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title_short',
        'user',
        'notification_type',
        'is_read',
        'created_at',
        'read_at'
    ]
    list_filter = ['is_read', 'notification_type', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at', 'read_at']
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Related Task', {
            'fields': ('todoist_task_id',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at', 'read_at')
        }),
    )

    def title_short(self, obj):
        if len(obj.title) > 60:
            return obj.title[:60] + '...'
        return obj.title
    title_short.short_description = 'Title'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
        self.message_user(request, f"{queryset.count()} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"


@admin.register(GeneratedTask)
class GeneratedTaskAdmin(admin.ModelAdmin):
    list_display = [
        'task_content_short',
        'template',
        'due_date',
        'is_completed',
        'generated_at'
    ]
    list_filter = ['is_completed', 'due_date', 'generated_at']
    search_fields = ['task_content', 'todoist_task_id', 'template__name']
    readonly_fields = ['generated_at']
    fieldsets = (
        ('Task Information', {
            'fields': ('template', 'todoist_task_id', 'task_content', 'due_date')
        }),
        ('Status', {
            'fields': ('is_completed', 'generated_at')
        }),
    )

    def task_content_short(self, obj):
        if len(obj.task_content) > 50:
            return obj.task_content[:50] + '...'
        return obj.task_content
    task_content_short.short_description = 'Task Content'
