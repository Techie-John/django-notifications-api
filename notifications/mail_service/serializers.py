from rest_framework import serializers


class SendEmailSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255, required=True)
    message = serializers.CharField(required=True)
    recipient_list = serializers.ListField(
        child=serializers.EmailField(),  # Ensure each recipient is a valid email address
        required=True
    )
    token = serializers.CharField(required=True)
    mail_action = serializers.BooleanField(default=False)
    firebase_action = serializers.BooleanField(default=False)
    is_schedule = serializers.BooleanField(default=False)
    deliver_time = serializers.DateTimeField(default=None)
    schedule_status = serializers.IntegerField(default=0)

