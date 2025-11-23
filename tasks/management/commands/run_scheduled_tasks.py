"""
Django management command to run scheduled tasks
Run this as a cron job for automated task management
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from tasks.models import (
    TaskTemplate,
    AutoCompleteRule,
    GeneratedTask
)
from tasks.todoist_client import TodoistClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run scheduled tasks: auto-complete overdue tasks and generate recurring tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-complete-only',
            action='store_true',
            help='Only run auto-complete tasks',
        )
        parser.add_argument(
            '--generate-only',
            action='store_true',
            help='Only generate recurring tasks',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting scheduled tasks...'))

        client = TodoistClient()

        if not options['generate_only']:
            self.auto_complete_tasks(client)

        if not options['auto_complete_only']:
            self.generate_recurring_tasks(client)

        self.stdout.write(self.style.SUCCESS('Scheduled tasks completed!'))

    def auto_complete_tasks(self, client):
        """Auto-complete overdue tasks based on rules"""
        self.stdout.write('Checking for tasks to auto-complete...')

        # Get all active auto-complete rules
        rules = AutoCompleteRule.objects.filter(
            is_active=True,
            completed_at__isnull=True
        )

        completed_count = 0

        for rule in rules:
            try:
                # Get the task from Todoist
                task = client.get_task(rule.todoist_task_id)

                # Check if task has a due date and is overdue
                if task.get('due'):
                    due_date_str = task['due']['date']

                    # Parse due date (could be date only or datetime)
                    if 'T' in due_date_str:
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    else:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                        due_date = timezone.make_aware(due_date)

                    # Calculate the deadline including grace period
                    deadline = due_date + timedelta(hours=rule.complete_after_hours)
                    now = timezone.now()

                    if now >= deadline:
                        # Auto-complete the task
                        client.complete_task(rule.todoist_task_id)

                        # Update the rule
                        rule.completed_at = timezone.now()
                        rule.is_active = False
                        rule.save()

                        # Update generated task if exists
                        GeneratedTask.objects.filter(
                            todoist_task_id=rule.todoist_task_id
                        ).update(is_completed=True)

                        completed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Auto-completed: {rule.task_content}')
                        )

            except Exception as e:
                logger.error(f'Error auto-completing task {rule.todoist_task_id}: {e}')
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error with {rule.task_content}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Auto-completed {completed_count} tasks')
        )

    def generate_recurring_tasks(self, client):
        """Generate tasks from active templates"""
        self.stdout.write('Generating recurring tasks...')

        # Get all active templates
        templates = TaskTemplate.objects.filter(is_active=True)

        generated_count = 0

        for template in templates:
            try:
                # Determine if we should generate a new task
                should_generate = False
                now = timezone.now()

                if not template.last_generated:
                    # Never generated before, create first task
                    should_generate = True
                else:
                    # Check if enough time has passed based on frequency
                    time_since_last = now - template.last_generated

                    if template.frequency == 'daily' and time_since_last >= timedelta(days=1):
                        should_generate = True
                    elif template.frequency == 'weekly' and time_since_last >= timedelta(weeks=1):
                        should_generate = True
                    elif template.frequency == 'biweekly' and time_since_last >= timedelta(weeks=2):
                        should_generate = True
                    elif template.frequency == 'monthly' and time_since_last >= timedelta(days=30):
                        should_generate = True
                    elif template.frequency == 'yearly' and time_since_last >= timedelta(days=365):
                        should_generate = True

                if should_generate:
                    # Calculate next due date
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

                    task_description = None
                    if template.description_template:
                        task_description = template.description_template.format(
                            date=due_date.strftime('%Y-%m-%d'),
                            month=due_date.strftime('%B'),
                            day=due_date.strftime('%d'),
                            year=due_date.strftime('%Y')
                        )

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
                            created_by=template.created_by
                        )

                    # Update template
                    template.last_generated = timezone.now()
                    template.save()

                    generated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Generated: {task_content}')
                    )

            except Exception as e:
                logger.error(f'Error generating task from template {template.id}: {e}')
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error with template {template.name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Generated {generated_count} tasks from templates')
        )
