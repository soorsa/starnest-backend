import logging
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

class SendGridService:
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def send_email(self, to_email, subject, html_content, plain_text_content=None):
        """
        Send email using SendGrid
        """
        if not self.client:
            logger.error("SendGrid API key not configured")
            return False

        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content or self.html_to_text(html_content)
            )

            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def html_to_text(self, html_content):
        """
        Simple HTML to text conversion for plain text fallback
        """
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)
        # Replace multiple spaces with single space
        text = re.sub('\s+', ' ', text)
        return text.strip()


# Global instance
sendgrid_service = SendGridService()