import threading
from datetime import datetime
from django.contrib.auth import get_user_model
from django.conf import settings
from core.utils import send_html_email


def generate_password():
    return get_user_model().objects.make_random_password()


def generate_student_id():
    # Generate a username based on first and last name and registration date
    registered_year = datetime.now().strftime("%Y")
    students_count = get_user_model().objects.filter(is_student=True).count()
    return f"{settings.STUDENT_ID_PREFIX}-{registered_year}-{students_count}"


def generate_lecturer_id():
    # Generate a username based on first and last name and registration date
    registered_year = datetime.now().strftime("%Y")
    lecturers_count = get_user_model().objects.filter(is_lecturer=True).count()
    return f"{settings.LECTURER_ID_PREFIX}-{registered_year}-{lecturers_count}"


def generate_student_credentials():
    return generate_student_id(), generate_password()


def generate_lecturer_credentials():
    return generate_lecturer_id(), generate_password()


class EmailThread(threading.Thread):
    def __init__(self, subject, recipient_list, template_name, context):
        self.subject = subject
        self.recipient_list = recipient_list
        self.template_name = template_name
        self.context = context
        threading.Thread.__init__(self)

    def run(self):
        import time
        from django.core.mail import send_mail
        from smtplib import SMTPDataError
        import logging

        logger = logging.getLogger(__name__)
        max_retries = 3
        retry_delay = 3  # seconds

        for attempt in range(max_retries):
            try:
                time.sleep(retry_delay)  # Add a 3-second delay between emails
                send_html_email(
                    subject=self.subject,
                    recipient_list=self.recipient_list,
                    template=self.template_name,
                    context=self.context,
                )
                break  # If successful, break the retry loop
            except SMTPDataError as e:
                if "Too many emails per second" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Failed to send email after {max_retries} attempts: {str(e)}")
                    break
            except Exception as e:
                logger.error(f"Unexpected error sending email: {str(e)}")
                break


def send_new_account_email(user, password):
    if user.is_student:
        template_name = "accounts/email/new_student_account_confirmation.html"
    else:
        template_name = "accounts/email/new_lecturer_account_confirmation.html"
    email = {
        "subject": "Your LMS Analytics account confirmation and credentials",
        "recipient_list": [user.email],
        "template_name": template_name,
        "context": {"user": user, "password": password},
    }
    EmailThread(**email).start()
