# Generated by Django 5.1 on 2024-11-11 18:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mail_service", "0002_email_email_service_api_key_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="email",
            name="email_service_api_key",
        ),
        migrations.RemoveField(
            model_name="email",
            name="email_service_api_secret",
        ),
        migrations.RemoveField(
            model_name="email",
            name="email_service_name",
        ),
    ]
