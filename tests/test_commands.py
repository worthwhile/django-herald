"""
Testing custom commands
"""

from datetime import timedelta, datetime

from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from six import StringIO

from herald.models import SentNotification
from herald.management.commands.delnotifs import valid_date

MSG = "Successfully deleted {num} notification(s)"
NOTIFICATION_CLASS = "tests.notifications.MyNotification"


class DeleteNotification(TestCase):
    out = StringIO()
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def setUp(self):
        SentNotification(
            notification_class=NOTIFICATION_CLASS,
            date_sent=timezone.now() - timedelta(days=3),
        ).save()
        SentNotification(
            notification_class=NOTIFICATION_CLASS,
            date_sent=timezone.now() - timedelta(days=2),
        ).save()
        SentNotification(
            notification_class=NOTIFICATION_CLASS,
            date_sent=timezone.now() - timedelta(days=1),
        ).save()
        SentNotification(
            notification_class=NOTIFICATION_CLASS, date_sent=timezone.now()
        ).save()
        SentNotification(
            notification_class=NOTIFICATION_CLASS, date_sent=timezone.now()
        ).save()

    def test_date_validator(self):
        self.assertEqual(valid_date("2017-01-01"), datetime(2017, 1, 1))

    def test_delete_without_arg(self):
        call_command("delnotifs", stdout=self.out)
        self.assertIn(MSG.format(num=2), self.out.getvalue())

    def test_delete_start_end_range_args(self):
        two_days_ago = self.today - timedelta(days=2)
        call_command(
            "delnotifs", stdout=self.out, start=str(two_days_ago), end=str(self.today)
        )
        self.assertIn(MSG.format(num=2), self.out.getvalue())

    def test_start_date_only_arg(self):
        two_days_ago = self.today - timedelta(days=2)
        call_command("delnotifs", stdout=self.out, start=str(two_days_ago))
        self.assertIn(MSG.format(num=4), self.out.getvalue())

    def test_end_date_only_arg(self):
        one_days_ago = self.today - timedelta(days=1)
        call_command("delnotifs", stdout=self.out, end=str(one_days_ago))
        self.assertIn(MSG.format(num=2), self.out.getvalue())

    def test_do_accept_bad_args(self):
        SentNotification(
            notification_class=NOTIFICATION_CLASS,
            date_sent=self.today - timedelta(days=1),
        ).save()

        with self.assertRaises(ValidationError):
            call_command("delnotifs", stdout=self.out, start="blargh")

        with self.assertRaises(ValidationError):
            call_command("delnotifs", stdout=self.out, start="01-01-2016")
