# Generated by Django 2.0.5 on 2018-05-16 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("herald", "0004_auto_20171009_0906"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_class",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="notification",
            name="verbose_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
