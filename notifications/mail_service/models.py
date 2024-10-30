from django.db import models


class Email(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    token = models.TextField(default=None)
    recipient_list = models.TextField()  # Consider changing to JSON field or ManyToManyField if needed
    created_at = models.DateTimeField(auto_now_add=True)
    sent_mail_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    firebase_response = models.TextField(null=True, blank=True)
    mail_action = models.BooleanField(default=False)
    firebase_action = models.BooleanField(default=False)
    is_schedule = models.BooleanField(default=False)
    delivery_time = models.DateTimeField(null=True, blank=True)
    # When is_schedule = True, 0 is scheduled , 1 is canceled , 2 sent the message.
    schedule_status = models.IntegerField(default=0)

    def __str__(self):
        return self.subject
