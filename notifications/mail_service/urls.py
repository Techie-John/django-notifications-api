from django.urls import path
from .views import send_email, schedule_notification, cancel_notification

urlpatterns = [
    path('send-email/', send_email, name='send_email'),
    path('schedule-notification/', schedule_notification, name='schedule_notification'),
    path('cancel-notification/<str:job_id>/', cancel_notification, name='cancel_notification'),
]