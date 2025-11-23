"""
Views for chtodoist task management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta

from .todoist_client import TodoistClient
from .models import (
    TaskTemplate,
    AutoCompleteRule,
    TaskWatcher,
    Notification,
    GeneratedTask
)


# ===== AUTHENTICATION VIEWS =====

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'tasks/login.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ===== DASHBOARD VIEWS =====

@login_required
def dashboard(request):
    """
    Main dashboard showing tasks from Todoist with filtering options
    """
    client = TodoistClient()
    filter_type = request.GET.get('filter', 'all')

    try:
        # Fetch tasks based on filter
        if filter_type == 'today':
            tasks = client.get_today_tasks()
        elif filter_type == 'overdue':
            tasks = client.get_overdue_tasks()
        elif filter_type == 'week':
            tasks = client.get_upcoming_tasks(days=7)
        else:
            tasks = client.get_tasks()

        # Get projects for display
        projects = client.get_projects()
        project_dict = {p['id']: p for p in projects}

        # Enrich tasks with additional data
        for task in tasks:
            task['project_name'] = project_dict.get(task.get('project_id'), {}).get('name', 'Inbox')

            # Check if task has watchers
            task['watchers'] = TaskWatcher.objects.filter(
                todoist_task_id=task['id']
            ).select_related('watcher')

            # Check if task has auto-complete rule
            task['auto_complete_rule'] = AutoCompleteRule.objects.filter(
                todoist_task_id=task['id'],
                is_active=True
            ).first()

    except Exception as e:
        messages.error(request, f"Error fetching tasks from Todoist: {str(e)}")
        tasks = []
        projects = []

    # Get user's templates and notifications
    templates = TaskTemplate.objects.filter(is_active=True).order_by('-created_at')[:5]
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:10]

    context = {
        'tasks': tasks,
        'projects': projects,
        'templates': templates,
        'notifications': notifications,
        'filter_type': filter_type,
        'unread_count': notifications.count(),
    }

    return render(request, 'tasks/dashboard.html', context)


# ===== TASK TEMPLATE VIEWS =====

@login_required
def template_list(request):
    """List all task templates"""
    templates = TaskTemplate.objects.all().order_by('-created_at')
    return render(request, 'tasks/template_list.html', {'templates': templates})


@login_required
def template_create(request):
    """Create a new task template"""
    if request.method == 'POST':
        try:
            template = TaskTemplate.objects.create(
                name=request.POST['name'],
                content_template=request.POST['content_template'],
                description_template=request.POST.get('description_template', ''),
                project_id=request.POST.get('project_id', ''),
                frequency=request.POST['frequency'],
                priority=int(request.POST.get('priority', 1)),
                labels=request.POST.get('labels', ''),
                auto_complete=request.POST.get('auto_complete') == 'on',
                is_active=request.POST.get('is_active', 'on') == 'on',
                created_by=request.user
            )
            messages.success(request, f"Template '{template.name}' created successfully!")
            return redirect('template_list')
        except Exception as e:
            messages.error(request, f"Error creating template: {str(e)}")

    # Get projects for dropdown
    client = TodoistClient()
    try:
        projects = client.get_projects()
    except:
        projects = []

    return render(request, 'tasks/template_form.html', {
        'projects': projects,
        'frequencies': TaskTemplate.FREQUENCY_CHOICES
    })


@login_required
@require_POST
def template_generate(request, template_id):
    """Manually generate a task from a template"""
    template = get_object_or_404(TaskTemplate, id=template_id)
    client = TodoistClient()

    try:
        # Calculate next due date based on frequency
        now = timezone.now()
        if template.frequency == 'daily':
            due_date = now + timedelta(days=1)
        elif template.frequency == 'weekly':
            due_date = now + timedelta(weeks=1)
        elif template.frequency == 'biweekly':
            due_date = now + timedelta(weeks=2)
        elif template.frequency == 'monthly':
            due_date = now + timedelta(days=30)
        else:  # yearly
            due_date = now + timedelta(days=365)

        # Format task content with variables
        task_content = template.content_template.format(
            date=due_date.strftime('%Y-%m-%d'),
            month=due_date.strftime('%B'),
            day=due_date.strftime('%d'),
            year=due_date.strftime('%Y')
        )

        task_description = template.description_template.format(
            date=due_date.strftime('%Y-%m-%d'),
            month=due_date.strftime('%B'),
            day=due_date.strftime('%d'),
            year=due_date.strftime('%Y')
        ) if template.description_template else None

        # Create task in Todoist
        task = client.create_task(
            content=task_content,
            description=task_description,
            project_id=template.project_id if template.project_id else None,
            due_date=due_date.strftime('%Y-%m-%d'),
            priority=template.priority,
            labels=template.get_labels_list()
        )

        # Track generated task
        GeneratedTask.objects.create(
            template=template,
            todoist_task_id=task['id'],
            task_content=task_content,
            due_date=due_date.date()
        )

        # Create auto-complete rule if needed
        if template.auto_complete:
            AutoCompleteRule.objects.create(
                todoist_task_id=task['id'],
                task_content=task_content,
                complete_after_hours=0,
                created_by=request.user
            )

        # Update template
        template.last_generated = timezone.now()
        template.save()

        messages.success(request, f"Task '{task_content}' created successfully!")

    except Exception as e:
        messages.error(request, f"Error generating task: {str(e)}")

    return redirect('dashboard')


# ===== AUTO-COMPLETE VIEWS =====

@login_required
def autocomplete_list(request):
    """List all auto-complete rules"""
    rules = AutoCompleteRule.objects.filter(
        is_active=True,
        completed_at__isnull=True
    ).order_by('-created_at')

    return render(request, 'tasks/autocomplete_list.html', {'rules': rules})


@login_required
@require_POST
def autocomplete_create(request):
    """Create an auto-complete rule for a task"""
    try:
        task_id = request.POST['task_id']
        task_content = request.POST['task_content']
        hours = int(request.POST.get('hours', 0))

        rule, created = AutoCompleteRule.objects.get_or_create(
            todoist_task_id=task_id,
            defaults={
                'task_content': task_content,
                'complete_after_hours': hours,
                'created_by': request.user
            }
        )

        if created:
            messages.success(request, f"Auto-complete rule created for '{task_content}'")
        else:
            rule.is_active = True
            rule.save()
            messages.info(request, f"Auto-complete rule reactivated for '{task_content}'")

    except Exception as e:
        messages.error(request, f"Error creating auto-complete rule: {str(e)}")

    return redirect('dashboard')


# ===== TASK WATCHER VIEWS =====

@login_required
@require_POST
def watcher_add(request):
    """Add a watcher to a task"""
    try:
        task_id = request.POST['task_id']
        task_content = request.POST['task_content']
        watcher_username = request.POST['watcher_username']

        from django.contrib.auth.models import User
        watcher = User.objects.get(username=watcher_username)

        watcher_obj, created = TaskWatcher.objects.get_or_create(
            todoist_task_id=task_id,
            watcher=watcher,
            defaults={
                'task_content': task_content,
                'added_by': request.user
            }
        )

        if created:
            # Create notification for the watcher
            Notification.objects.create(
                user=watcher,
                notification_type='watcher_added',
                title=f"You were added as a watcher",
                message=f"{request.user.username} added you as a watcher to: {task_content}",
                todoist_task_id=task_id
            )
            messages.success(request, f"{watcher_username} added as watcher")
        else:
            messages.info(request, f"{watcher_username} is already watching this task")

    except User.DoesNotExist:
        messages.error(request, f"User '{watcher_username}' not found")
    except Exception as e:
        messages.error(request, f"Error adding watcher: {str(e)}")

    return redirect('dashboard')


@login_required
@require_POST
def watcher_remove(request, watcher_id):
    """Remove a watcher from a task"""
    watcher = get_object_or_404(TaskWatcher, id=watcher_id)

    # Only the person who added the watcher or the watcher themselves can remove
    if request.user == watcher.added_by or request.user == watcher.watcher:
        watcher.delete()
        messages.success(request, "Watcher removed")
    else:
        return HttpResponseForbidden("You don't have permission to remove this watcher")

    return redirect('dashboard')


# ===== NOTIFICATION VIEWS =====

@login_required
def notifications_view(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tasks/notifications.html', {'notifications': notifications})


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def notification_mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    messages.success(request, "All notifications marked as read")
    return redirect('notifications')


# ===== TASK COMPLETION =====

@login_required
@require_POST
def task_complete(request, task_id):
    """Complete a task in Todoist"""
    client = TodoistClient()
    try:
        client.complete_task(task_id)

        # Notify watchers
        watchers = TaskWatcher.objects.filter(
            todoist_task_id=task_id,
            notify_on_complete=True
        )
        for watcher in watchers:
            Notification.objects.create(
                user=watcher.watcher,
                notification_type='task_completed',
                title="Task completed",
                message=f"Task '{watcher.task_content}' was completed",
                todoist_task_id=task_id
            )

        messages.success(request, "Task completed!")
    except Exception as e:
        messages.error(request, f"Error completing task: {str(e)}")

    return redirect('dashboard')
