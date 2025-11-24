# auth-mail-sendgrid
Django authentication and Sendgrid mail integration
# Django SendGrid Task Email App

A Django application for managing tasks with automatic email notifications via SendGrid. When a task is marked as completed, an email is automatically sent to the task creator with completion details.

## Features

- ✅ **Task Management** — Create, assign, and track tasks
- 📧 **Automatic Email Notifications** — SendGrid integration for reliable email delivery
- 🔔 **Real-time Alerts** — Instant notifications when tasks are completed
- 📱 **User-friendly Interface** — Simple Django views for task operations
- 🎨 **HTML Email Templates** — Professional formatted emails with task details
- 🔐 **Secure** — Uses Django's signal system for safe, decoupled email sending

## Requirements

- Python 3.8+
- Django 3.2+
- sendgrid-django

## Installation

### 1. Install Dependencies

```bash
pip install sendgrid-django
```

### 2. Set Up SendGrid Account

1. Sign up for a free SendGrid account at [https://sendgrid.com](https://sendgrid.com)
2. Verify your sender email address in Settings > Sender Authentication
3. Generate an API key:
   - Navigate to Settings > API Keys
   - Click "Create API Key"
   - Give it a name (e.g., "Django App")
   - Copy the key to a safe location

### 3. Configure Django Settings

Add the following to your `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'tasks',
]

# Email Configuration
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = 'your-sendgrid-api-key-here'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'  # Use your verified sender email
```

**Security Note:** Store your API key in environment variables for production:

```python
import os
from decouple import config

SENDGRID_API_KEY = config('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Add URLs to Your Project

In your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... your other patterns
    path('tasks/', include('tasks.urls')),
]
```

## Usage

### Create a Task

```python
from tasks.models import Task
from django.contrib.auth.models import User

creator = User.objects.get(username='john')
assignee = User.objects.get(username='jane')

task = Task.objects.create(
    title='Complete project documentation',
    description='Write comprehensive docs for the API',
    created_by=creator,
    assigned_to=assignee,
    status='pending'
)
```

### Mark Task as Completed

When you mark a task as completed, the email is automatically sent:

```python
from django.utils import timezone

task.status = 'completed'
task.completed_at = timezone.now()
task.save(update_fields=['status', 'completed_at'])
# Email automatically sent to task.created_by at this point
```

Or use the view:

```python
POST /tasks/{task_id}/complete/
```

### Available Views

- `GET /tasks/` — List all assigned tasks
- `GET /tasks/create/` — Create task form
- `POST /tasks/create/` — Submit new task
- `POST /tasks/{id}/complete/` — Mark task as completed

## Email Customization

To customize the email template, edit the `send_completion_email()` function in `tasks/signals.py`:

```python
def send_completion_email(task):
    subject = f"Task Completed: {task.title}"
    
    html_message = f"""
    <html>
        <body>
            <!-- Customize your HTML here -->
            <h2>Task Complete!</h2>
            <p>Task: {task.title}</p>
        </body>
    </html>
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [task.created_by.email],
        html_message=html_message,
    )
```

## Project Structure

```
tasks/
├── migrations/          # Database migrations
├── __init__.py
├── models.py           # Task model definition
├── signals.py          # Email sending logic
├── views.py            # Request handlers
├── urls.py             # URL routing
├── apps.py             # App configuration
└── admin.py            # Django admin setup
```

## Models

### Task

| Field | Type | Description |
|-------|------|-------------|
| `title` | CharField | Task title (max 200 characters) |
| `description` | TextField | Detailed task description |
| `status` | CharField | One of: pending, in_progress, completed, cancelled |
| `assigned_to` | ForeignKey | User assigned to complete the task |
| `created_by` | ForeignKey | User who created the task |
| `created_at` | DateTimeField | Task creation timestamp |
| `completed_at` | DateTimeField | Task completion timestamp |

## How It Works

1. **Task Creation** — A user creates a task and assigns it to another user
2. **Task Completion** — The assigned user marks the task as completed
3. **Signal Triggered** — Django's `post_save` signal detects the status change
4. **Email Sent** — An email is automatically composed and sent via SendGrid to the task creator
5. **Notification Received** — Task creator receives formatted email with completion details

## Error Handling

The email sending is wrapped in a try-except block. If an email fails to send, an error message is printed but the task update completes successfully. To implement better error handling in production, consider using a task queue like Celery:

```bash
pip install celery redis
```

Then update `signals.py` to use Celery tasks for asynchronous email sending.

## Testing

### Manual Testing

```python
# Django Shell
python manage.py shell

from django.contrib.auth.models import User
from tasks.models import Task
from django.utils import timezone

user1 = User.objects.create_user(username='alice', email='alice@example.com')
user2 = User.objects.create_user(username='bob', email='bob@example.com')

task = Task.objects.create(
    title='Test Task',
    description='This is a test',
    created_by=user1,
    assigned_to=user2
)

# Mark as completed - email will be sent
task.status = 'completed'
task.completed_at = timezone.now()
task.save(update_fields=['status', 'completed_at'])
```

### Verify SendGrid Integration

1. Check your SendGrid dashboard at [https://app.sendgrid.com/activity](https://app.sendgrid.com/activity)
2. Look for recent email activity
3. Click on emails to view delivery status

## Troubleshooting

**Issue: "InvalidRequest: Invalid Twilio SendGrid credentials"**
- Check that your `SENDGRID_API_KEY` is correct
- Verify the API key hasn't expired

**Issue: "BadRequest: Invalid from email"**
- Ensure the email in `DEFAULT_FROM_EMAIL` is verified in SendGrid Settings
- Use the exact email you verified during setup

**Issue: Emails not being sent**
- Check SendGrid Activity page for bounce/delivery issues
- Verify recipient email addresses are valid
- Check Django logs for error messages
- Ensure `EMAIL_BACKEND` is correctly configured

**Issue: Development/Testing**
- Use SendGrid's sandbox mode in tests
- Or configure EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' for development (prints emails to console)

## Production Checklist

- [ ] Set `DEBUG = False`
- [ ] Store API keys in environment variables (use `python-decouple` or similar)
- [ ] Verify sender email domain in SendGrid
- [ ] Set up SendGrid IP warming if using dedicated IP
- [ ] Configure email categories in SendGrid for better tracking
- [ ] Set up bounce/complaint handling
- [ ] Test email delivery to multiple recipients
- [ ] Implement Celery for async email sending (optional but recommended)
- [ ] Set up monitoring and alerting for failed emails

## Contributing

Feel free to fork, submit issues, and create pull requests to improve this app.

## License

MIT License - Feel free to use this in your projects.

## Support

For SendGrid-specific issues, visit the [SendGrid documentation](https://docs.sendgrid.com).
For Django issues, see the [Django documentation](https://docs.djangoproject.com).

## Changelog

### Version 1.0.0
- Initial release
- Task management with CRUD operations
- SendGrid email integration
- Automatic email on task completion
- HTML email templates
