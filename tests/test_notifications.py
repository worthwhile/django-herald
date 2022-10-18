from datetime import timedelta

import jsonpickle
from django.core import mail
from django.core.files import File
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.test import TestCase, override_settings
from django.utils import timezone
from herald.base import EmailNotification, NotificationBase, TwilioTextNotification
from herald.models import SentNotification

from mock import patch

from .notifications import MyNotification, MyNotificationAttachmentOpen

try:
    # twilio version 6
    from twilio.rest.api.v2010.account import MessageList
except ImportError:
    # twillio version < 6
    from twilio.rest.resources import Messages as MessageList


class BaseNotificationTests(TestCase):
    def test_get_context_data(self):
        self.assertDictEqual(
            MyNotification().get_context_data(),
            {"hello": "world", "base_url": "http://example.com", "subject": None},
        )

    def test_get_recipients(self):
        self.assertRaises(NotImplementedError, NotificationBase().get_recipients)

    def test_get_extra_data(self):
        self.assertDictEqual(NotificationBase().get_extra_data(), {})

    def test_get_sent_from(self):
        self.assertRaises(NotImplementedError, NotificationBase().get_sent_from)

    def test_get_subject(self):
        self.assertIsNone(NotificationBase().get_subject())

    def test_get_demo_args(self):
        self.assertListEqual(NotificationBase.get_demo_args(), [])

    def test_private_send(self):
        self.assertRaises(NotImplementedError, NotificationBase()._send, [])

    def test_get_attachments(self):
        self.assertIsNone(NotificationBase().get_attachments())

    def test_send(self):
        with patch.object(MyNotification, "resend") as mocked_resend:
            MyNotification().send()
            mocked_resend.assert_called_once()
            obj = mocked_resend.call_args[0][0]
            self.assertEqual(obj.recipients, "test@test.com")

    @override_settings(HERALD_RAISE_MISSING_TEMPLATES=False)
    def test_send_no_text(self):
        class DummyNotification(EmailNotification):
            render_types = ["html"]
            to_emails = ["test@test.com"]

        with patch.object(DummyNotification, "resend") as mocked_resend:
            DummyNotification().send()
            mocked_resend.assert_called_once()
            obj = mocked_resend.call_args[0][0]
            self.assertEqual(obj.recipients, "test@test.com")
            self.assertIsNone(obj.text_content)

    def test_real_send(self):
        MyNotification().send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@test.com"])

    def test_real_send_attachments(self):
        MyNotification().send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0][1], "Some Report Data")

    def test_real_send_attachments_open(self):
        MyNotificationAttachmentOpen().send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0][0], "tests/python.jpeg")
        self.assertEqual(mail.outbox[0].attachments[1][0], "tests/python.jpeg")

    def test_render_no_type(self):
        class DummyNotification(NotificationBase):
            pass

        with self.assertRaises(AssertionError):
            DummyNotification().render("text", {})

    @override_settings(HERALD_RAISE_MISSING_TEMPLATES=False)
    def test_render_invalid_template(self):
        class DummyNotification(NotificationBase):
            render_types = ["text"]
            template_name = "does_not_exist"

        self.assertIsNone(DummyNotification().render("text", {}))

    @override_settings(DEBUG=True)
    def test_render_invalid_template_debug(self):
        class DummyNotification(NotificationBase):
            render_types = ["text"]
            template_name = "does_not_exist"

        with self.assertRaises(TemplateDoesNotExist):
            DummyNotification().render("text", {})

    def test_render_invalid(self):
        class DummyNotification(NotificationBase):
            render_types = ["text"]
            template_name = "hello_world"

        self.assertEqual(DummyNotification().render("text", {}), "Hello World")

    def test_resend_error(self):
        notification = SentNotification()

        with patch.object(NotificationBase, "_send") as mocked__send:
            mocked__send.side_effect = Exception
            result = NotificationBase.resend(notification)
            self.assertFalse(result)

    def test_resend_error_raise(self):
        notification = SentNotification()

        with patch.object(NotificationBase, "_send") as mocked__send:
            mocked__send.side_effect = Exception
            self.assertRaises(
                Exception, NotificationBase.resend, notification, raise_exception=True
            )

    def test_resend(self):
        notification = SentNotification()

        with patch.object(NotificationBase, "_send") as mocked__send:
            result = NotificationBase.resend(notification)
            self.assertTrue(result)

    def test_get_verbose_name(self):
        class TestNotification(EmailNotification):
            pass

        self.assertEqual(TestNotification.get_verbose_name(), "Test Notification")

        class TestNotification2(EmailNotification):
            verbose_name = "A verbose name"

        self.assertEqual(TestNotification2.get_verbose_name(), "A verbose name")

    def test_get_encoded_attachments_none(self):
        class TestNotification(EmailNotification):
            attachments = []

        self.assertJSONEqual(TestNotification()._get_encoded_attachments(), [])

    def test_get_encoded_attachments_basic(self):
        class TestNotification(EmailNotification):
            attachments = [("Report.txt", "raw_data", "text/plain")]

        self.assertJSONEqual(
            TestNotification()._get_encoded_attachments(),
            [{"py/tuple": ["Report.txt", "raw_data", "text/plain"]}],
        )

    def test_get_encoded_attachments_file(self):
        class TestNotification(EmailNotification):
            attachments = [File(open("tests/python.jpeg", "rb"))]

        attachments = jsonpickle.loads(TestNotification()._get_encoded_attachments())
        self.assertEqual(attachments[0][0], "tests/python.jpeg")
        self.assertEqual(attachments[0][2], "image/jpeg")

    def test_delete_notifications_no_setting(self):
        # create a test notification from a long time ago
        SentNotification.objects.create(
            recipients="test@test.com",
            date_sent=timezone.now() - timedelta(weeks=52),
            notification_class="MyNotification",
        )
        # create a test notification from recently
        SentNotification.objects.create(
            recipients="test@test.com",
            date_sent=timezone.now() - timedelta(weeks=10),
            notification_class="MyNotification",
        )
        MyNotification().send()
        # all three were not deleted because we didn't have a setting
        self.assertEqual(SentNotification.objects.count(), 3)

    @override_settings(HERALD_NOTIFICATION_RETENTION_TIME=timedelta(weeks=26))
    def test_delete_notifications(self):
        # create a test notification from a long time ago
        n1 = SentNotification.objects.create(
            recipients="test@test.com",
            date_sent=timezone.now() - timedelta(weeks=52),
            notification_class="MyNotification",
        )
        # create a test notification from recently
        n2 = SentNotification.objects.create(
            recipients="test@test.com",
            date_sent=timezone.now() - timedelta(weeks=10),
            notification_class="MyNotification",
        )
        MyNotification().send()

        # the one from a year ago was deleted, but not the one from 10 weeks ago.
        self.assertEqual(SentNotification.objects.count(), 2)
        ids = SentNotification.objects.values_list("id", flat=True)
        self.assertTrue(n2.id in ids)
        self.assertFalse(n1.id in ids)


class EmailNotificationTests(TestCase):
    def test_get_recipients(self):
        self.assertListEqual(MyNotification().get_recipients(), ["test@test.com"])

    def test_get_sent_from(self):
        class TestNotification(EmailNotification):
            from_email = "bob@example.com"

        self.assertEqual(TestNotification().get_sent_from(), "bob@example.com")

    def test_get_sent_from_default(self):
        class TestNotification(EmailNotification):
            from_email = None

        with override_settings(DEFAULT_FROM_EMAIL="default@example.com"):
            self.assertEqual(TestNotification().get_sent_from(), "default@example.com")

    def test_get_subject(self):
        class TestNotification(EmailNotification):
            subject = "test subject"

        self.assertEqual(TestNotification().get_subject(), "test subject")

    def test_get_extra_data_none(self):
        self.assertDictEqual(EmailNotification().get_extra_data(), {})

    def test_get_extra_data(self):
        class TestNotification(EmailNotification):
            bcc = "bcc@test.com"
            cc = "cc@test.com"
            headers = {"HEADER": "test"}
            reply_to = "reply_to@test.com"

        self.assertDictEqual(
            TestNotification().get_extra_data(),
            {
                "bcc": "bcc@test.com",
                "cc": "cc@test.com",
                "headers": {"HEADER": "test"},
                "reply_to": "reply_to@test.com",
            },
        )

    @override_settings(HERALD_HTML2TEXT_ENABLED=True)
    def test_render_html2text(self):
        class TestNotificationHTML2Text(EmailNotification):
            template_name = "hello_world_html2text"

        output = TestNotificationHTML2Text().render(render_type="text", context={})
        self.assertEqual(output, "# Hello World\n\n")

        # Also test with DEBUG on so TemplateDoesNotExist is thrown
        with override_settings(DEBUG=True):
            output = TestNotificationHTML2Text().render(render_type="text", context={})
            self.assertEqual(output, "# Hello World\n\n")

    def test_send_html_content(self):
        class TestNotification(EmailNotification):
            subject = "test subject"

        with patch.object(
            EmailMultiAlternatives, "attach_alternative"
        ) as mocked_attach_alternative:
            TestNotification._send([], text_content="Text")
            mocked_attach_alternative.assert_not_called()

        with patch.object(
            EmailMultiAlternatives, "attach_alternative"
        ) as mocked_attach_alternative:
            TestNotification._send([], html_content="Text")
            mocked_attach_alternative.assert_called_once_with("Text", "text/html")


class TwilioNotificationTests(TestCase):
    def test_get_recipients(self):
        class TestNotification(TwilioTextNotification):
            to_number = "1231231234"

        self.assertListEqual(TestNotification().get_recipients(), ["1231231234"])

    def test_get_sent_from(self):
        class TestNotification(TwilioTextNotification):
            from_number = "1231231234"

        self.assertEqual(TestNotification().get_sent_from(), "1231231234")

    def test_get_sent_from_default(self):
        class TestNotification(TwilioTextNotification):
            from_number = None

        with override_settings(TWILIO_DEFAULT_FROM_NUMBER="1231231234"):
            self.assertEqual(TestNotification().get_sent_from(), "1231231234")

    def test_get_sent_from_default_error(self):
        class TestNotification(TwilioTextNotification):
            from_number = None

        self.assertRaisesMessage(
            Exception,
            "TWILIO_DEFAULT_FROM_NUMBER setting is required for sending a TwilioTextNotification",
            TestNotification().get_sent_from,
        )

    @override_settings(TWILIO_ACCOUNT_SID="sid", TWILIO_AUTH_TOKEN="token")
    def test_send(self):
        class TestNotification(TwilioTextNotification):
            from_number = "1231231234"
            to_number = "1231231234"
            template_name = "hello_world"

        with patch.object(MessageList, "create") as mocked_create:
            TestNotification().send()
            mocked_create.assert_called_once_with(
                body="Hello World", to="1231231234", from_="1231231234"
            )

    @override_settings(TWILIO_ACCOUNT_SID="sid", TWILIO_AUTH_TOKEN="token")
    def test_sending_to_multiple_numbers(self):
        class TestNotification(TwilioTextNotification):
            from_number = "1231231234"
            template_name = "hello_world"

            def get_recipients(self):
                return ["1234567890", "0987654321"]

        with patch.object(MessageList, "create") as mocked_create:
            notification = TestNotification()
            notification.send()
            self.assertEqual(mocked_create.call_count, 2)
            for recipient in notification.get_recipients():
                mocked_create.assert_any_call(
                    body="Hello World", to=recipient, from_=notification.get_sent_from()
                )

    def test_send_no_settings(self):
        class TestNotification(TwilioTextNotification):
            from_number = "1231231234"
            to_number = "1231231234"
            template_name = "hello_world"

        with self.assertRaisesMessage(
            Exception,
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN settings are required for "
            "sending a TwilioTextNotification",
        ):
            TestNotification().send(raise_exception=True)
