
# Email and Notification API

This API allows users to send emails and Firebase push notifications instantly or schedule them for future delivery. It utilizes Django and the Django REST Framework, along with Firebase for push notifications.

## Features
- Send emails using Django's email capabilities.
- Send push notifications via Firebase.
- Schedule emails and notifications for future delivery.
- Cancel scheduled emails and notifications.

## Support Email Service Provider
- Brevo
- MailerSend
- Mailgun
- Mailjet
- Mandrill
- Postal
- Postmark
- Resend
- SendGrid
- SparkPost
- Unisender Go

## Requirements
- Python 3.6+
- Django
- Django REST Framework
- Firebase Admin SDK
- APScheduler

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/LYTE-studios/django-notifications-api.git
    cd django-notifications-api/notifications
    ```

2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up Firebase:
    - Create a Firebase project and obtain your service account credentials.
    - Save your credentials file as `credentials.json` in the appropriate directory.

5. Run the migrations to set up the database:
    ```bash
    python manage.py migrate
    ```

6. Start the server:
    ```bash
    python manage.py runserver
    ```

## API Endpoints

### 1. Send Email

- **Endpoint**: `/api/send_email/`
- **Method**: `POST`
- **Description**: Sends an email and optionally sends a push notification via Firebase.
- **Request Header**: `X-Email-Service`, `X-Email-Service-API-Key`, `X-Email-Service-API-Secret` 
- **Firebase Credential JSON** : If you want to notification, You have to send firebase credential JSON file with name `credential_file`
#### **Request Body (JSON)**
```json
{
    "subject": "Email Subject",
    "message": "Email Body",
    "recipient_list": ["recipient@example.com"],
    "token": "firebase_device_token",
    "mail_action": true,
    "firebase_action": false
}
```

#### **Response**
- **Success** (HTTP 200):
```json
{
    "status": "Notification sent!",
    "record": { ... }
}
```
- **Error** (HTTP 400):
```json
{
    "errors": {
        "field_name": ["error message"]
    }
}
```
- **Error** (HTTP 500):
```json
{
    "error": "Error description"
}
```

### 2. Schedule Notification

- **Endpoint**: `/api/schedule_notification/`
- **Method**: `POST`
- **Description**: Schedules an email and/or a push notification via Firebase to be sent at a specified delivery time.
- **Request Header**: `X-Email-Service`, `X-Email-Service-API-Key`, `X-Email-Service-API-Secret` 
- **Firebase Credential JSON** : If you want to notification, You have to send firebase credential JSON file with name `credential_file`

#### **Request Body (JSON)**
```json
{
    "subject": "Scheduled Email Subject",
    "message": "Scheduled Email Body",
    "recipient_list": ["recipient@example.com"],
    "token": "firebase_device_token",
    "mail_action": true,
    "firebase_action": false,
    "delivery_time": "2024-10-30T15:30:45.123456"  // Example ISO format
}
```

#### **Response**
- **Success** (HTTP 200):
```json
{
    "status": "event scheduled!",
    "schedule id": 1
}
```
- **Error** (HTTP 400):
```json
{
    "errors": "You have to put mail action for firebase action"
}
```
- **Error** (HTTP 500):
```json
{
    "error": "Error description"
}
```

### 3. Cancel Scheduled Email/Notification

- **Endpoint**: `/api/cancel_notification/<job_id>/`
- **Method**: `DELETE`
- **Description**: Cancels a scheduled email or notification.

#### **URL Parameters**
- `job_id` (int): The ID of the scheduled job.

#### **Response**
- **Success** (HTTP 200):
```json
{
    "status": "Scheduled notification canceled!"
}
```
- **Error** (HTTP 404):
```json
{
    "status": "Job ID not found."
}
```
- **Error** (HTTP 500):
```json
{
    "status": "An error occurred: Error description"
}
```

## Notes
- **Request Validation**: Input data is validated using the `SendEmailSerializer`. Ensure that the request body adheres to the expected format.
- **Firebase Token**: Ensure that the Firebase token is valid for push notifications.
- **Error Handling**: The application provides error messages for various failure points.

## Conclusion
This API provides a flexible interface for sending emails and push notifications, along with the ability to schedule these actions for specific times. Ensure that you handle authentication and permissions as needed within your application for added security.
