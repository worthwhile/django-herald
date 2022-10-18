from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from mock import patch

from herald.models import SentNotification


class ViewsTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        self.client = Client()
        self.client.login(username="admin", password="password")
        self.notification = SentNotification.objects.create(
            recipients="test@example.com",
            date_sent=timezone.now(),
            status=SentNotification.STATUS_SUCCESS,
            notification_class="tests.notifications.MyNotification",
        )

    def test_index(self):
        response = self.client.get(reverse("admin:herald_sentnotification_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        response = self.client.get(
            reverse(
                "admin:herald_sentnotification_change", args=(self.notification.pk,)
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_resend(self):
        with patch.object(SentNotification, "resend") as mocked_resend:
            response = self.client.get(
                reverse(
                    "admin:herald_sentnotification_resend", args=(self.notification.pk,)
                ),
                follow=True,
            )
            mocked_resend.assert_called_once()

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "The notification was resent successfully.",
            [m.message for m in list(response.context["messages"])],
        )

    def test_resend_fail(self):
        with patch.object(SentNotification, "resend") as mocked_resend:
            mocked_resend.return_value = False
            response = self.client.get(
                reverse(
                    "admin:herald_sentnotification_resend", args=(self.notification.pk,)
                ),
                follow=True,
            )
            mocked_resend.assert_called_once()

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "The notification failed to resend.",
            [m.message for m in list(response.context["messages"])],
        )
