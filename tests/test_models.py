import six
from mock import patch

from django.test import TestCase

from herald.models import SentNotification, Notification
from tests.notifications import MyNotification


class SentNotificationTests(TestCase):
    def test_str(self):
        notification = SentNotification(
            notification_class="tests.notifications.MyNotification"
        )
        self.assertEqual(
            six.text_type(notification), "tests.notifications.MyNotification"
        )

    def test_get_recipients(self):
        notification = SentNotification(recipients="test@test.com,example@example.com")
        self.assertListEqual(
            notification.get_recipients(), ["test@test.com", "example@example.com"]
        )

    def test_get_extra_data_none(self):
        notification = SentNotification()
        self.assertDictEqual(notification.get_extra_data(), {})

    def test_get_extra_data(self):
        notification = SentNotification(extra_data='{"something":["one","two"]}')
        self.assertDictEqual(
            notification.get_extra_data(), {"something": ["one", "two"]}
        )

    def test_resend(self):
        notification = SentNotification(
            notification_class="tests.notifications.MyNotification"
        )
        with patch.object(MyNotification, "resend") as mocked_resend:
            notification.resend()
            mocked_resend.assert_called_once_with(notification)


class NotificationTests(TestCase):
    def test_str(self):
        notification = Notification(
            notification_class="tests.notifications.MyNotification"
        )
        self.assertEqual(
            six.text_type(notification), "tests.notifications.MyNotification"
        )
