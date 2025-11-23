# CLAUDE.md - AI Assistant Guide for chtodoist

## Project Overview

**chtodoist** is a custom web application designed to enhance task management for the Worship Arts team at Cherry Hills Church in Springfield, IL (www.cherryhillsfamily.org). The application builds upon Todoist's API to solve specific workflow challenges that the native Todoist application doesn't address.

### Core Mission
Create a user-friendly web interface that extends Todoist's functionality to support:
- Multi-user task assignments with automatic notifications
- Custom recurring tasks with dynamic naming (e.g., tasks with dates in the name)
- Automatic task completion after due dates
- Simplified navigation and task management interface

---

## Current Project State

**Status**: Early stage - project planning and documentation phase

**Repository Contents**:
- `README.md` - Basic project description
- `Project.md` - Detailed project objectives and technical specifications
- `CLAUDE.md` - This file (AI assistant guide)

**What's Missing**: The actual application code is not yet implemented.

---

## Technical Stack

### Framework Decision
Choose between **Flask** or **Django** based on:

**Flask** - Recommended if:
- Lightweight, minimal structure preferred
- Quick prototyping needed
- Simple API integration is primary goal
- Team prefers flexibility over convention

**Django** - Recommended if:
- Built-in admin panel would be valuable
- User authentication/authorization needed
- ORM for complex data relationships desired
- Following convention-over-configuration philosophy

### Core Technologies
- **Language**: Python 3.x
- **Web Framework**: Flask or Django (TBD)
- **API Integration**: Todoist REST API v2
- **Deployment Platform**: Railway.com
- **Authentication**: User login system with admin capabilities

---

## Todoist API Configuration

### API Credentials
**API Token**: `8426c819aa2e15accc4d119c7a42e309d93c1733`

### Security Best Practices
⚠️ **IMPORTANT**: This API key is currently documented here for development purposes, but should be moved to environment variables before deployment:

```python
# DON'T hardcode in source files
api_token = "8426c819aa2e15accc4d119c7a42e309d93c1733"  # ❌

# DO use environment variables
import os
api_token = os.getenv('TODOIST_API_TOKEN')  # ✅
```

**Action Items**:
1. Create `.env` file for local development (add to `.gitignore`)
2. Configure environment variables on Railway.com
3. Use python-dotenv or similar for loading env vars
4. Never commit API keys to version control

### Todoist API Resources
- **Documentation**: https://developer.todoist.com/rest/v2/
- **Python SDK**: https://github.com/Doist/todoist-api-python
- **API Version**: REST API v2

---

## Key Problems to Solve

### 1. Enhanced UI/UX for Task Management
**Problem**: Current Todoist interface is not intuitive for the team's workflow
**Solution Approach**:
- Create simplified dashboard with focused views
- Implement custom filtering and sorting options
- Design team-specific task organization

### 2. Multi-User Task Assignment
**Problem**: Todoist doesn't support assigning multiple people to one task
**Solution Approach**:
- Create task "watchers" system in addition to assignee
- Implement notification system for all watchers
- Track completion status and send alerts on missed deadlines
- Consider using Todoist's comments/labels as metadata storage

### 3. Dynamic Recurring Task Names
**Problem**: Recurring tasks can't have custom names per occurrence
**Solution Approach**:
- Use Todoist API to create tasks programmatically
- Implement templating system for task names (e.g., "Weekly Report - {date}")
- Schedule background job to generate upcoming occurrences
- Store template definitions in application database

### 4. Automatic Task Completion After Due Date
**Problem**: No auto-complete functionality for overdue tasks
**Solution Approach**:
- Implement scheduled job (cron/celery) to check due dates
- Add "auto-complete" flag to task metadata (using labels/description)
- Automatically close tasks after due date passes
- Particularly useful for recurring tasks that shouldn't pile up

---

## Architecture Guidelines

### Recommended Project Structure

```
chtodoist/
├── app/
│   ├── __init__.py
│   ├── models.py          # Database models (if using local DB)
│   ├── todoist_api.py     # Todoist API wrapper/client
│   ├── routes.py          # URL routing and views
│   ├── tasks.py           # Background tasks/scheduled jobs
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, images
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (gitignored)
├── .gitignore
├── README.md
├── Project.md
└── CLAUDE.md
```

### Data Storage Strategy

**Option 1: Todoist as Source of Truth**
- Store all metadata using Todoist's labels, descriptions, comments
- Pros: No separate database needed, simpler deployment
- Cons: Limited by Todoist's data structure, harder queries

**Option 2: Hybrid Approach (Recommended)**
- Use local database for app-specific data (watchers, templates, settings)
- Sync with Todoist for tasks and projects
- Pros: Flexibility, better querying, richer features
- Cons: Need to handle synchronization

**Option 3: Full Local Database**
- Mirror Todoist data locally, sync periodically
- Pros: Maximum flexibility and performance
- Cons: Complex sync logic, potential data inconsistencies

---

## Development Workflows

### Setting Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd chtodoist

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "TODOIST_API_TOKEN=8426c819aa2e15accc4d119c7a42e309d93c1733" > .env
echo "FLASK_ENV=development" >> .env
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env

# Run development server
python run.py  # or flask run / python manage.py runserver
```

### Git Workflow

**Branch Naming Convention**:
- Feature branches: `claude/feature-name-{sessionId}`
- Bug fixes: `claude/fix-name-{sessionId}`
- Documentation: `claude/docs-name-{sessionId}`

**Commit Message Format**:
```
<type>: <description>

[optional body]

Types: feat, fix, docs, refactor, test, chore
```

**Development Process**:
1. Create feature branch from main
2. Implement changes with clear commits
3. Test locally with development API token
4. Push to origin with: `git push -u origin <branch-name>`
5. Create pull request for review

---

## Coding Conventions

### Python Style
- Follow PEP 8 style guide
- Use type hints for function signatures
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable names (no single letters except loop counters)

### Code Organization Principles
- **Keep it simple**: Avoid over-engineering
- **YAGNI**: You Aren't Gonna Need It - don't add features before they're needed
- **DRY**: Don't Repeat Yourself - extract common patterns
- **Explicit over implicit**: Clear code beats clever code

### Error Handling
```python
# Handle API errors gracefully
try:
    response = todoist_api.get_tasks()
except requests.exceptions.RequestException as e:
    logger.error(f"Todoist API error: {e}")
    flash("Unable to fetch tasks. Please try again.")
    return redirect(url_for('dashboard'))
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Task created successfully")
logger.warning("Approaching API rate limit")
logger.error("Failed to sync with Todoist")
```

---

## Testing Strategy

### Test Categories
1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test Todoist API interactions
3. **End-to-End Tests**: Test complete user workflows

### Testing Todoist Integration
- Use separate Todoist project for testing
- Mock API responses for unit tests
- Use test API token for integration tests (if available)
- Clean up test data after test runs

### Example Test Structure
```python
import unittest
from app import create_app
from app.todoist_api import TodoistClient

class TestTodoistIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = TodoistClient(test_token)

    def test_fetch_tasks(self):
        tasks = self.client.get_tasks()
        self.assertIsInstance(tasks, list)

    def tearDown(self):
        # Clean up test data
        pass
```

---

## Todoist API Integration Patterns

### Basic API Client Structure
```python
import requests
from typing import List, Dict, Optional

class TodoistClient:
    BASE_URL = "https://api.todoist.com/rest/v2"

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def get_tasks(self, project_id: Optional[str] = None) -> List[Dict]:
        """Fetch tasks, optionally filtered by project"""
        url = f"{self.BASE_URL}/tasks"
        params = {"project_id": project_id} if project_id else {}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def create_task(self, content: str, **kwargs) -> Dict:
        """Create a new task"""
        url = f"{self.BASE_URL}/tasks"
        data = {"content": content, **kwargs}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_task(self, task_id: str, **kwargs) -> Dict:
        """Update an existing task"""
        url = f"{self.BASE_URL}/tasks/{task_id}"
        response = requests.post(url, headers=self.headers, json=kwargs)
        response.raise_for_status()
        return response.json()

    def complete_task(self, task_id: str) -> bool:
        """Mark task as complete"""
        url = f"{self.BASE_URL}/tasks/{task_id}/close"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return True
```

### Implementing Multi-User Assignments
Since Todoist doesn't natively support this, use task description or comments:

```python
def assign_multiple_users(self, task_id: str, user_emails: List[str]):
    """Assign multiple watchers to a task using description metadata"""
    watchers_tag = f"[WATCHERS:{','.join(user_emails)}]"

    # Get current task
    task = self.get_task(task_id)
    description = task.get('description', '')

    # Add watchers tag to description
    new_description = f"{description}\n{watchers_tag}".strip()

    # Update task
    self.update_task(task_id, description=new_description)

    # Notify watchers (implement notification system)
    for email in user_emails:
        self.notify_user(email, task)
```

### Implementing Dynamic Recurring Tasks
```python
from datetime import datetime, timedelta

def create_recurring_task_from_template(
    self,
    template: str,
    frequency: str,
    project_id: str
):
    """
    Create tasks from template with dynamic names
    template example: "Weekly Report - {date:%Y-%m-%d}"
    frequency: "weekly", "daily", "monthly"
    """
    # Calculate next occurrence dates
    next_date = datetime.now() + timedelta(days=7)  # Example: weekly

    # Format task name with actual date
    task_name = template.format(date=next_date)

    # Create task
    self.create_task(
        content=task_name,
        project_id=project_id,
        due_date=next_date.strftime("%Y-%m-%d")
    )
```

---

## Deployment on Railway.com

### Railway Configuration
1. **Connect Repository**: Link GitHub repo to Railway
2. **Environment Variables**: Set in Railway dashboard
   - `TODOIST_API_TOKEN`
   - `SECRET_KEY`
   - `DATABASE_URL` (if using PostgreSQL)
   - `FLASK_ENV=production` or `DJANGO_SETTINGS_MODULE`

3. **Procfile/Start Command**:
```
# For Flask
web: gunicorn app:app

# For Django
web: gunicorn myproject.wsgi:application
```

4. **Dependencies**: Ensure `requirements.txt` includes production dependencies
```
# requirements.txt
Flask==3.0.0  # or Django==5.0.0
gunicorn==21.2.0
requests==2.31.0
python-dotenv==1.0.0
# ... other dependencies
```

### Background Jobs
For scheduled tasks (auto-completion, recurring task generation):
- Use Railway cron jobs or
- Implement with APScheduler (simpler) or Celery (more robust)

```python
# Example with APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

def auto_complete_overdue_tasks():
    """Run daily to auto-complete tasks past due date"""
    # Implementation here
    pass

scheduler = BackgroundScheduler()
scheduler.add_job(auto_complete_overdue_tasks, 'cron', hour=0)
scheduler.start()
```

---

## AI Assistant Guidelines

### When Working on This Project

**DO**:
- ✅ Read existing documentation (Project.md, README.md) before making changes
- ✅ Ask clarifying questions if requirements are ambiguous
- ✅ Follow the established project structure
- ✅ Write clear, documented code with type hints
- ✅ Handle Todoist API errors gracefully
- ✅ Respect API rate limits (implement backoff if needed)
- ✅ Keep security in mind (never hardcode secrets)
- ✅ Test integrations before committing
- ✅ Use meaningful commit messages
- ✅ Update this CLAUDE.md if you discover new patterns or conventions

**DON'T**:
- ❌ Over-engineer solutions
- ❌ Add features not requested in Project.md without discussion
- ❌ Commit API keys or sensitive data
- ❌ Make breaking changes without noting them
- ❌ Ignore error handling
- ❌ Skip documentation for complex logic
- ❌ Push directly to main branch

### Understanding Context
Before implementing features, understand:
1. **User Base**: Worship Arts team at a church (likely non-technical users)
2. **Primary Goal**: Simplify task management, not replace Todoist entirely
3. **Constraints**: Working within Todoist's API limitations
4. **Deployment**: Self-hosted on Railway.com

### Making Decisions
When faced with technical choices:
1. **Prioritize simplicity** - This is a team tool, not a SaaS product
2. **Consider maintainability** - Small team context
3. **Respect constraints** - Todoist API limitations are real
4. **Ask when uncertain** - Better to clarify than assume

### Communication Style
When explaining code or decisions:
- Use clear, concise language
- Provide examples
- Explain "why" not just "what"
- Reference line numbers: `file_path:line_number`

---

## Common Tasks Reference

### Adding a New Feature
1. Review Project.md to ensure it aligns with project goals
2. Design the feature considering Todoist API constraints
3. Update CLAUDE.md if introducing new patterns
4. Implement with proper error handling
5. Test with actual Todoist API
6. Document any new API usage patterns
7. Commit and push to feature branch

### Debugging Todoist Integration Issues
```python
# Enable request logging
import logging
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

### Checking API Rate Limits
Todoist has rate limits - implement monitoring:
```python
def make_api_request(self, method, url, **kwargs):
    """Wrapper to monitor rate limits"""
    response = requests.request(method, url, headers=self.headers, **kwargs)

    # Check rate limit headers
    remaining = response.headers.get('X-RateLimit-Remaining')
    if remaining and int(remaining) < 10:
        logger.warning(f"API rate limit low: {remaining} requests remaining")

    response.raise_for_status()
    return response
```

---

## Future Considerations

### Potential Enhancements
- Mobile-responsive design for on-the-go access
- Real-time notifications via WebSockets
- Team analytics and reporting dashboard
- Integration with church calendar systems
- Bulk task operations
- Task templates library
- Email notifications for missed deadlines

### Scalability Notes
Current scope is for a single team/church. If expanding:
- Implement multi-tenancy
- Add more robust authentication (OAuth, SSO)
- Consider caching layer for Todoist data
- Implement webhook listeners for real-time sync
- Add database indexing for performance

---

## Resources

### Documentation
- [Todoist REST API v2](https://developer.todoist.com/rest/v2/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Railway Docs](https://docs.railway.app/)

### Community
- [Todoist API Community](https://github.com/Doist/todoist-api-python/discussions)
- [Flask Discord](https://discord.gg/flask)
- [Python Discord](https://discord.gg/python)

---

## Changelog

### [Unreleased]
- Initial project setup and documentation

---

## Contact & Support

**Project Owner**: Cherry Hills Church - Worship Arts Team
**Repository**: chtodoist
**Deployment**: Railway.com

For questions or issues, consult Project.md or create GitHub issues for tracking.

---

*Last Updated: 2025-11-23*
*AI Assistant: Claude (Anthropic)*
