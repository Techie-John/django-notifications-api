from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from .models import Email
from .serializers import SendEmailSerializer
from rest_framework import status
import json
import datetime

class TestSendEmailView(TestCase):

    def setUp(self):
        self.client = Client()
        self.valid_data = {
            'subject': 'Test Email',
            'message': 'This is a test email',
            'recipient_list': ['test@example.com'],
            'token': 'test_token',
            'mail_action': True,
            'firebase_action': False,
            'email_service_name': 'Mailjet',
            'email_service_api_key': 'test_api_key',
            'email_service_api_secret': 'test_api_secret'
        }
        self.invalid_data = {
            'subject': '',
            'message': '',
            'recipient_list': [],
            'token': '',
            'mail_action': False,
            'firebase_action': False
        }

    def test_send_email_valid_data(self):
        response = self.client.post(reverse('send_email'), self.valid_data, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_send_email_invalid_data(self):
        response = self.client.post(reverse('send_email'), self.invalid_data, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestScheduleNotificationView(TestCase):

    def setUp(self):
        self.client = Client()
        self.valid_data = {
            'subject': 'Test Email',
            'message': 'This is a test email',
            'recipient_list': ['test@example.com'],
            'token': 'test_token',
            'mail_action': True,
            'firebase_action': False,
            'email_service_name': 'Mailjet',
            'email_service_api_key': 'test_api_key',
            'email_service_api_secret': 'test_api_secret',
            'delivery_time': '2024-12-31T23:59:59Z'
        }
        self.invalid_data = {
            'subject': '',
            'message': '',
            'recipient_list': [],
            'token': '',
            'mail_action': False,
            'firebase_action': False
        }

    def test_schedule_notification_valid_data(self):
        response = self.client.post(reverse('schedule_notification'), self.valid_data, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_schedule_notification_invalid_data(self):
        response = self.client.post(reverse('schedule_notification'), self.invalid_data, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestCancelNotificationView(TestCase):

    def setUp(self):
        self.client = Client()
        self.email = Email.objects.create(
            subject='Test Email',
            message='This is a test email',
            recipient_list='test@example.com',
            token='test_token',
            mail_action=True,
            firebase_action=False,
            is_schedule=True,
            delivery_time='2024-12-31T23:59:59Z'
        )

    def test_cancel_notification_valid_job_id(self):
        response = self.client.delete(reverse('cancel_notification', args=[self.email.id]), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_notification_invalid_job_id(self):
        response = self.client.delete(reverse('cancel_notification', args=[999]), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)