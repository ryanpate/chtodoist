"""
Todoist API Client for chtodoist project
Handles all interactions with the Todoist REST API v2
"""
import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class TodoistClient:
    """Client for interacting with Todoist REST API v2"""

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.TODOIST_API_TOKEN
        self.base_url = settings.TODOIST_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to Todoist API with error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/tasks')
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: On API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )

            # Check rate limits
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining and int(remaining) < 10:
                logger.warning(f"API rate limit low: {remaining} requests remaining")

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Todoist API error: {method} {endpoint} - {e}")
            raise

    # ===== PROJECT OPERATIONS =====

    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        response = self._make_request('GET', '/projects')
        return response.json()

    def get_project(self, project_id: str) -> Dict:
        """Get a specific project"""
        response = self._make_request('GET', f'/projects/{project_id}')
        return response.json()

    # ===== TASK OPERATIONS =====

    def get_tasks(self, project_id: Optional[str] = None, filter_query: Optional[str] = None) -> List[Dict]:
        """
        Get tasks, optionally filtered by project or query

        Args:
            project_id: Filter by project ID
            filter_query: Todoist filter string (e.g., 'today', 'overdue')

        Returns:
            List of task dictionaries
        """
        params = {}
        if project_id:
            params['project_id'] = project_id
        if filter_query:
            params['filter'] = filter_query

        response = self._make_request('GET', '/tasks', params=params)
        return response.json()

    def get_task(self, task_id: str) -> Dict:
        """Get a specific task"""
        response = self._make_request('GET', f'/tasks/{task_id}')
        return response.json()

    def create_task(
        self,
        content: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        due_string: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: int = 1,
        labels: Optional[List[str]] = None,
        **kwargs
    ) -> Dict:
        """
        Create a new task

        Args:
            content: Task name/content
            description: Task description
            project_id: Project to add task to
            due_string: Natural language due date (e.g., "tomorrow", "next Monday")
            due_date: ISO 8601 formatted date (YYYY-MM-DD)
            priority: Priority level (1-4, 4 is highest)
            labels: List of label names
            **kwargs: Additional task parameters

        Returns:
            Created task dictionary
        """
        data = {
            "content": content,
            **kwargs
        }

        if description:
            data["description"] = description
        if project_id:
            data["project_id"] = project_id
        if due_string:
            data["due_string"] = due_string
        elif due_date:
            data["due_date"] = due_date
        if priority > 1:
            data["priority"] = priority
        if labels:
            data["labels"] = labels

        response = self._make_request('POST', '/tasks', json=data)
        return response.json()

    def update_task(self, task_id: str, **kwargs) -> Dict:
        """
        Update an existing task

        Args:
            task_id: ID of task to update
            **kwargs: Fields to update (content, description, due_date, etc.)

        Returns:
            Updated task dictionary
        """
        response = self._make_request('POST', f'/tasks/{task_id}', json=kwargs)
        return response.json()

    def complete_task(self, task_id: str) -> bool:
        """
        Mark task as complete

        Args:
            task_id: ID of task to complete

        Returns:
            True if successful
        """
        self._make_request('POST', f'/tasks/{task_id}/close')
        logger.info(f"Task {task_id} marked as complete")
        return True

    def reopen_task(self, task_id: str) -> bool:
        """
        Reopen a completed task

        Args:
            task_id: ID of task to reopen

        Returns:
            True if successful
        """
        self._make_request('POST', f'/tasks/{task_id}/reopen')
        logger.info(f"Task {task_id} reopened")
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task

        Args:
            task_id: ID of task to delete

        Returns:
            True if successful
        """
        self._make_request('DELETE', f'/tasks/{task_id}')
        logger.info(f"Task {task_id} deleted")
        return True

    # ===== COMMENT OPERATIONS =====

    def get_comments(self, task_id: str) -> List[Dict]:
        """Get all comments for a task"""
        response = self._make_request('GET', '/comments', params={'task_id': task_id})
        return response.json()

    def add_comment(self, task_id: str, content: str) -> Dict:
        """
        Add a comment to a task

        Args:
            task_id: ID of task
            content: Comment text

        Returns:
            Created comment dictionary
        """
        data = {
            "task_id": task_id,
            "content": content
        }
        response = self._make_request('POST', '/comments', json=data)
        return response.json()

    # ===== LABEL OPERATIONS =====

    def get_labels(self) -> List[Dict]:
        """Get all labels"""
        response = self._make_request('GET', '/labels')
        return response.json()

    def create_label(self, name: str, color: Optional[str] = None) -> Dict:
        """Create a new label"""
        data = {"name": name}
        if color:
            data["color"] = color
        response = self._make_request('POST', '/labels', json=data)
        return response.json()

    # ===== UTILITY METHODS =====

    def get_overdue_tasks(self) -> List[Dict]:
        """Get all overdue tasks"""
        return self.get_tasks(filter_query='overdue')

    def get_today_tasks(self) -> List[Dict]:
        """Get tasks due today"""
        return self.get_tasks(filter_query='today')

    def get_upcoming_tasks(self, days: int = 7) -> List[Dict]:
        """Get tasks due in the next N days"""
        return self.get_tasks(filter_query=f'{days} days')
