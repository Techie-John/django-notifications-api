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
        delivery_time = request.data.get('delivery_time')  # Expecting ISO format
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
        if mail_action is False and firebase_action is False:
            return Response({"errors : you have to put mail action for firebase action"},
                            status=status.HTTP_400_BAD_REQUEST)

        if mail_action:
            # Create a new Email record with status 'pending'

            try:
                email_record.sent_mail_status = 'pending'
                email_record.save()
                scheduler.add_job(send_email_message, 'date', run_date=delivery_time,
                                  args=[subject, message, recipient_list, email_backend])

            except Exception as e:
                # Update status to 'failed'
                email_record.sent_mail_status = 'failed'
                email_record.save()

                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if firebase_action:

            try:
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
                # Save the notification details to the database

                email_record.firebase_response = "pending"
                email_record.save()

                schedule_id = email_record.id
                scheduler.add_job(message_firebase, 'date', run_date=delivery_time,
                                  args=[subject, message, token, credential_path])

                return Response({"status": "event scheduled!", "schedule id": schedule_id}, status=status.HTTP_200_OK)

            except Exception as e:
                email_record.firebase_response = str(e)
                email_record.save()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# Cancel Scheduled Email/Notification
@api_view(['DELETE'])
def cancel_notification(request, job_id):
    try:
        # Step 1: Attempt to find the email record using job_id
        email_record = Email.objects.get(id=job_id)

        # Step 2: Update the schedule_status to 1 (canceled)
        email_record.schedule_status = 1
        email_record.save()

        # Step 3: Remove the job from the scheduler if necessary
        scheduler.remove_job(job_id)  # Assuming scheduler is a globally accessible object

        return Response({"status": "Scheduled notification canceled!"}, status=status.HTTP_200_OK)

    except Email.DoesNotExist:
        # Handle the case where the job_id does not correspond to an existing record
        return Response({"status": "Job ID not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Handle any other exceptions that may occur
        return Response({"status": "An error occurred: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Start the scheduler
scheduler.start()
