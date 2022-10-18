from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from herald.contrib.auth.forms import HeraldPasswordResetForm


class ContribAuthTests(TestCase):
    def test_save_form(self):
        User = get_user_model()
        User.objects.create_user(
            username="test@example.com", email="test@example.com", password="password"
        )
        form = HeraldPasswordResetForm({"email": "test@example.com"})
        form.is_valid()
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])

    def test_save_form_domain_override(self):
        User = get_user_model()
        User.objects.create_user(
            username="test@example.com", email="test@example.com", password="password"
        )
        form = HeraldPasswordResetForm({"email": "test@example.com"})
        form.is_valid()
        form.save(domain_override="foo")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
