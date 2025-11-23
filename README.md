# chtodoist

Custom task management application for Cherry Hills Church Worship Arts team, built on top of Todoist API.

## Features

- **Recurring Tasks with Custom Names**: Create task templates with dynamic naming (e.g., "Weekly Report - 2025-11-30")
- **Auto-Complete Tasks**: Automatically complete tasks after their due date
- **Multi-User Task Watching**: Assign multiple team members to watch tasks and receive notifications
- **Simplified Dashboard**: Clean, easy-to-navigate interface for managing tasks
- **In-App Notifications**: Stay updated on task changes, completions, and assignments

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chtodoist
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env` (if available) or create `.env` with:
   ```
   TODOIST_API_TOKEN=your_todoist_api_token
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main app: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Key Features Usage

### Creating Recurring Task Templates

1. Navigate to **Templates** in the navigation menu
2. Click **Create New Template**
3. Fill in the template details:
   - **Template Name**: Descriptive name for your reference
   - **Content Template**: Use variables like `{date}`, `{month}`, `{day}`, `{year}`
     - Example: `"Weekly Report - {date}"` becomes `"Weekly Report - 2025-11-30"`
   - **Frequency**: Daily, Weekly, Bi-weekly, Monthly, or Yearly
   - **Auto-complete**: Check to auto-complete tasks after due date
4. Click **Create Template**

### Generating Tasks from Templates

**Manual Generation:**
- From the Templates page, click **Generate** next to any template
- From the Dashboard, click **Generate Task** on template cards

**Automatic Generation:**
- Run the scheduled task command: `python manage.py run_scheduled_tasks`
- Set up as a cron job for automation (see Deployment section)

### Auto-Completing Tasks

1. From the Dashboard, find the task you want to auto-complete
2. Click **Auto-complete** button
3. Set hours after due date (0 = immediate)
4. The task will be automatically completed by the scheduled task runner

### Multi-User Assignments

1. From the Dashboard, find a task
2. Click **Add Watcher**
3. Enter the username of the team member
4. They will receive an in-app notification

## Background Tasks

The application includes automated background tasks for:
- Auto-completing overdue tasks
- Generating recurring tasks from templates

**Run manually:**
```bash
python manage.py run_scheduled_tasks
```

**Run specific tasks:**
```bash
# Only auto-complete tasks
python manage.py run_scheduled_tasks --auto-complete-only

# Only generate recurring tasks
python manage.py run_scheduled_tasks --generate-only
```

**Set up cron job (recommended):**
```bash
# Add to crontab (runs every hour)
0 * * * * cd /path/to/chtodoist && python manage.py run_scheduled_tasks
```

## Deployment to Railway.com

1. **Prepare your Railway project**
   - Sign up at https://railway.app
   - Create a new project
   - Connect your GitHub repository

2. **Set environment variables in Railway**
   ```
   TODOIST_API_TOKEN=your_todoist_api_token
   SECRET_KEY=your_production_secret_key
   DEBUG=False
   ALLOWED_HOSTS=your-app.railway.app
   ```

3. **Railway will automatically**
   - Detect the Django project
   - Install dependencies from `requirements.txt`
   - Run migrations
   - Start the application with gunicorn

4. **Create superuser on Railway**
   ```bash
   railway run python manage.py createsuperuser
   ```

5. **Set up scheduled tasks**
   - Use Railway's Cron Jobs feature
   - Or set up an external cron service to call: `railway run python manage.py run_scheduled_tasks`

## Project Structure

```
chtodoist/
├── chtodoist_project/     # Django project settings
│   ├── settings.py        # Configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI configuration
├── tasks/                 # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── urls.py            # App URL routing
│   ├── admin.py           # Admin configuration
│   ├── todoist_client.py  # Todoist API wrapper
│   ├── templates/         # HTML templates
│   └── management/        # Custom management commands
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── Procfile               # Railway/Heroku deployment
├── runtime.txt            # Python version
└── railway.json           # Railway configuration
```

## API Integration

The application uses the Todoist REST API v2. The API client is in `tasks/todoist_client.py`.

Key operations:
- Fetch tasks and projects
- Create, update, and complete tasks
- Add comments and labels
- Rate limit monitoring

## Database Models

- **TaskTemplate**: Templates for recurring tasks with dynamic naming
- **AutoCompleteRule**: Rules for auto-completing tasks
- **TaskWatcher**: Multi-user task assignments
- **Notification**: In-app notifications
- **GeneratedTask**: Track tasks generated from templates

## Admin Interface

Access the Django admin at `/admin/` to:
- Manage users
- View and edit all models
- Bulk operations on templates and rules
- Monitor notifications

## Troubleshooting

**Tasks not appearing:**
- Check your Todoist API token is correct
- Verify the token has proper permissions
- Check Django logs for API errors

**Auto-complete not working:**
- Ensure the scheduled task is running (`run_scheduled_tasks`)
- Verify tasks have due dates set
- Check auto-complete rules are active

**Template generation issues:**
- Check template variables syntax: `{date}`, `{month}`, `{day}`, `{year}`
- Verify project IDs are valid
- Check template is marked as active

## Contributing

See `CLAUDE.md` for detailed development guidelines and AI assistant instructions.

## License

Copyright Cherry Hills Church - Worship Arts Team

## Support

For issues or questions, contact your team administrator.
