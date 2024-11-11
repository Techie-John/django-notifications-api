from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import firebase_admin
from firebase_admin import credentials, messaging
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from .models import Email  # Import your Email model
from .serializers import SendEmailSerializer  # Import your serializer
import os
from .email_service import get_dynamic_email_backend
from anymail.message import AnymailMessage
import json
from firebase_admin import credentials, initialize_app, exceptions
from django.core.files.storage import default_storage
import uuid
import datetime


def initialize_firebase(credential_path):
    """Initialize Firebase with the given credential path."""
    try:
        cred = credentials.Certificate(credential_path)
        if not firebase_admin._apps:  # Check if Firebase is already initialized
            initialize_app(cred)
        else:
            raise Exception("Firebase has already been initialized.")
    except exceptions.FirebaseError as e:
        # Handle error accordingly, e.g., log it or return an error response
        print(f"Error initializing Firebase: {e}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
scheduler = BackgroundScheduler()


def send_email_message(subject, message, recipient_list, email_backend):
    # Create the email message
    email = AnymailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
        connection=email_backend
    )
    # Send the email
    email.send()


def message_firebase(subject, message, token, credential_path):
    initialize_firebase(credential_path)
    firebase_message = messaging.Message(
        notification=messaging.Notification(
            title=subject,
            body=message,
        ),
        token=token,
    )
    messaging.send(firebase_message)


# Send Email endpoint
@api_view(['POST'])
def send_email(request):
    # get service name and api key and api secret
    service_name = request.email_service_name
    api_key = request.email_service_api_key
    api_secret = request.email_service_api_secret if service_name == 'Mailjet' else None
    mail_credentials = {'api_key': api_key}
    if api_secret:
        mail_credentials['api_secret'] = api_secret

    if not service_name or not api_key or (service_name == 'Mailjet' and not api_secret):
        return Response({"error": "Service name, API key, and API secret (for Mailjet) must be provided."}, status=400)

    email_backend = get_dynamic_email_backend(service_name, mail_credentials)

    # Use the custom serializer to validate the input data
    serializer = SendEmailSerializer(data=request.data)

    if serializer.is_valid():

        subject = serializer.validated_data['subject']
        message = serializer.validated_data['message']
        recipient_list = serializer.validated_data['recipient_list']
        token = serializer.validated_data['token']
        mail_action = serializer.validated_data['mail_action']
        firebase_action = serializer.validated_data['firebase_action']
        email_record = Email.objects.create(
            subject=subject,
            message=message,
            recipient_list=','.join(recipient_list),
            token=token,
            firebase_response='',
            sent_mail_status='pending',  # Initial status,
            mail_action=mail_action,
            firebase_action=firebase_action

        )
        if mail_action is False and firebase_action is False:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if mail_action:
            # Create a new Email record with status 'pending'

            try:
                # Send the email
                send_email_message(subject, message, recipient_list, email_backend)

                # Update status to 'sent'
                email_record.sent_mail_status = 'sent'
                email_record.save()
                if firebase_action is False:
                    return Response({"status": "Email sent!", "record": serializer.data},
                                    status=status.HTTP_200_OK)

            except Exception as e:
                # Update status to 'failed'
                email_record.sent_mail_status = 'failed'
                email_record.save()

                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if firebase_action:
            file = request.FILES.get('credential_file')
            if not file:
                return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

            # Create uploads directory if it does not exist
            os.makedirs(UPLOADS_DIR, exist_ok=True)

            # Generate a random UUID and use it as the filename
            random_filename = f"{uuid.uuid4()}.json"  # Generates a UUID and appends '.json'
            credential_path = os.path.join(UPLOADS_DIR, random_filename)

            # Save the new credentials file to the uploads directory
            with default_storage.open(credential_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

                # Optional: Initialize Firebase or any other processing needed here
            initialize_firebase(credential_path)

            firebase_message = messaging.Message(
                notification=messaging.Notification(
                    title=subject,
                    body=message,
                ),
                token=token,
            )

            try:
                response = messaging.send(firebase_message)

                # Save the notification details to the database

                email_record.firebase_response = response
                email_record.save()

                return Response({"status": "Email and Notification sent!", "record": serializer.data},
                                status=status.HTTP_200_OK)

            except Exception as e:
                email_record.firebase_response = str(e)
                email_record.save()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# Schedule Email/Notification
@api_view(['POST'])
def schedule_notification(request):
    """
    Schedule an email/notification.

    Args:
        request (Request): Django request object.

    Returns:
        Response: JSON response with schedule status.
    """
    # Get service credentials
    service_name = request.data.get('email_service_name')
    api_key = request.data.get('email_service_api_key')
    api_secret = request.data.get('email_service_api_secret')

    # Validate service credentials
    if not service_name or not api_key or (service_name == 'Mailjet' and not api_secret):
        return Response({"error": "Service name, API key, and API secret (for Mailjet) must be provided."}, status=400)

    # Get email backend
    mail_credentials = {'api_key': api_key}
    if api_secret:
        mail_credentials['api_secret'] = api_secret
    email_backend = get_dynamic_email_backend(service_name, mail_credentials)

    # Validate input data
    serializer = SendEmailSerializer(data=request.data)
    if serializer.is_valid():
        subject = serializer.validated_data['subject']
        message = serializer.validated_data['message']
        recipient_list = serializer.validated_data['recipient_list']
        token = serializer.validated_data['token']
        mail_action = serializer.validated_data['mail_action']
        firebase_action = serializer.validated_data['firebase_action']
        delivery_time = request.data.get('delivery_time')  # Expecting ISO format

        # Validate delivery time
        try:
            delivery_time = datetime.strptime(delivery_time, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return Response({"error": "Invalid delivery time format."}, status=400)

        # Create email record
        email_record = Email.objects.create(
            subject=subject,
            message=message,
            recipient_list=','.join(recipient_list),
            token=token,
            firebase_response='',
            sent_mail_status='pending',  # Initial status,
            mail_action=mail_action,
            firebase_action=firebase_action,
            is_schedule=True,
            delivery_time=delivery_time
        )

        # Validate mail and firebase actions
        if not mail_action and not firebase_action:
            return Response({"error": "You must choose at least one action."}, status=400)

        try:
            # Schedule email
            if mail_action:
                scheduler.add_job(send_email_message, 'date', run_date=delivery_time,
                                  args=[subject, message, recipient_list, email_backend])

            # Schedule firebase notification
            if firebase_action:
                file = request.FILES.get('credential_file')
                if not file:
                    return Response({"error": "No file provided."}, status=400)

                # Save credential file
                os.makedirs(UPLOADS_DIR, exist_ok=True)
                random_filename = f"{uuid.uuid4()}.json"
                credential_path = os.path.join(UPLOADS_DIR, random_filename)
                with default_storage.open(credential_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                # Schedule job
                scheduler.add_job(message_firebase, 'date', run_date=delivery_time,
                                  args=[subject, message, token, credential_path])

            # Update email record status
            email_record.sent_mail_status = 'scheduled'
            email_record.save()

            return Response({"status": "Event scheduled!", "schedule id": email_record.id}, status=200)

        except Exception as e:
            # Update email record status
            email_record.sent_mail_status = 'failed'
            email_record.save()
            return Response({"error": str(e)}, status=500)

    return Response({"errors": serializer.errors}, status=400)


# Cancel Scheduled Email/Notification
@api_view(['DELETE'])
def cancel_notification(request, job_id):
    """
    Cancel a scheduled email/notification.

    Args:
        request (Request): Django request object.
        job_id (int): ID of the scheduled job.

    Returns:
        Response: JSON response with cancel status.
    """
    try:
        # Get email record
        email_record = Email.objects.get(id=job_id)

        # Update schedule status
        email_record.schedule_status = 1
        email_record.save()

        # Remove job from scheduler
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        return Response({"status": "Scheduled notification canceled!"}, status=200)

    except Email.DoesNotExist:
        return Response({"status": "Job ID not found."}, status=404)
    except Exception as e:
        return Response({"status": "An error occurred: " + str(e)}, status=500)


# Start the scheduler
scheduler.start()