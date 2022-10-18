from django.contrib.auth import get_user_model
from django.test import TestCase

from herald.models import SentNotification, UserNotification, Notification
from .notifications import MyNotification, MyOtherNotification


class UserNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()

        # create a user who does not want to get MyOtherNotification
        user = User(username="test", password="Safepass1.")
        user.save()
        usernotification = UserNotification(user=user)
        usernotification.save()

        # refresh the user
        self.user = User.objects.get(id=user.id)
        # add a notification
        notification = Notification(
            notification_class=MyOtherNotification.get_class_path()
        )
        notification.save()

        # disable the notification
        self.user.usernotification.disabled_notifications.add(notification)
        self.user = User.objects.get(id=user.id)

    def test_send_disabled(self):
        result = MyOtherNotification().send(user=self.user)
        self.assertTrue(result, True)

        sent_notification = SentNotification.objects.all()[0]
        self.assertEqual(
            sent_notification.status, sent_notification.STATUS_USER_DISABLED
        )

    def test_send_enabled(self):
        result = MyNotification().send(user=self.user)
        self.assertTrue(result, True)

        sent_notification = SentNotification.objects.all()[0]
        self.assertEqual(sent_notification.status, sent_notification.STATUS_SUCCESS)


class UserNotificationTestsNoSetting(TestCase):
    def setUp(self):
        User = get_user_model()

        # create a user who does not want to get MyOtherNotification
        self.user = User(username="test", password="Safepass1.")
        self.user.save()

    def test_send_enabled(self):
        result = MyNotification().send(user=self.user)
        self.assertTrue(result, True)

        sent_notification = SentNotification.objects.all()[0]
        self.assertEqual(sent_notification.status, sent_notification.STATUS_SUCCESS)
