from django.template.loader import render_to_string
from .services import sendgrid_service

def send_welcome_email(user_email, user_name,first_name,last_name):
    """
    Send task completion email
    """
    context = {
        'user_name': user_name,
        'email': user_email,
        'first_name':first_name,
        'last_name':last_name
    }
    
    html_content = render_to_string('emails/task_completed.html', context)
    
    subject = f"Welcome to APP_NAME: {first_name}"
    
    return sendgrid_service.send_email(
        to_email=user_email,
        subject=subject,
        html_content=html_content
    )

