from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email_task(recipient, subject, body):
    send_mail(subject, body, 'from@example.com', [recipient])