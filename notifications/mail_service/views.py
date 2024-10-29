from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import messaging
from django.utils import timezone
import datetime
from .tasks import send_email_task

class SendEmailView(APIView):
    def post(self, request):
        email_data = request.data
        send_email_task.delay(email_data['recipient'], email_data['subject'], email_data['body'])
        return Response({"message": "Email scheduled for sending."}, status=status.HTTP_201_CREATED)

class SendNotificationView(APIView):
    def post(self, request):
        notification_data = request.data
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification_data['title'],
                body=notification_data['body'],
            ),
            token=notification_data['token'],
        )
        response = messaging.send(message)
        return Response({"message": "Notification sent.", "response": response})

class ScheduleEmailView(APIView):
    def post(self, request):
        # Implement logic to schedule the email using a task queue (like Celery)
        return Response({"message": "Email scheduled."})

class CancelScheduledView(APIView):
    def delete(self, request, task_id):
        # Cancel the scheduled email/notification here
        return Response({"message": "Scheduled task cancelled."})