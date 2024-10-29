from django.urls import path
from .views import SendEmailView, SendNotificationView, ScheduleEmailView, CancelScheduledView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Mail Notifications API",
      default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('send-email/', SendEmailView.as_view(), name='send_email'),
    path('send-notification/', SendNotificationView.as_view(), name='send_notification'),
    path('schedule-email/', ScheduleEmailView.as_view(), name='schedule_email'),
    path('cancel/<int:task_id>/', CancelScheduledView.as_view(), name='cancel_task'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]