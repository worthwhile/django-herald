# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SentNotification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("text_content", models.TextField(null=True, blank=True)),
                ("html_content", models.TextField(null=True, blank=True)),
                ("sent_from", models.CharField(max_length=100, null=True, blank=True)),
                ("recipients", models.CharField(max_length=2000)),
                ("subject", models.CharField(max_length=255, null=True, blank=True)),
                ("extra_data", models.TextField(null=True, blank=True)),
                ("date_sent", models.DateTimeField()),
                (
                    "status",
                    models.PositiveSmallIntegerField(
                        default=0,
                        choices=[(0, "Pending"), (1, "Success"), (2, "Failed")],
                    ),
                ),
                ("notification_class", models.CharField(max_length=255)),
                (
                    "error_message",
                    models.CharField(max_length=255, null=True, blank=True),
                ),
            ],
        ),
    ]
