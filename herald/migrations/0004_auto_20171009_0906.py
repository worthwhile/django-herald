# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-09 14:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("herald", "0003_auto_20170830_1617"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sentnotification",
            name="error_message",
            field=models.TextField(blank=True, null=True),
        ),
    ]
