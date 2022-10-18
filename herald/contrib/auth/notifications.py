"""
Herald notifications for working with django.contrib.auth
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.template import loader
from django.utils.encoding import force_bytes

try:
    from django.utils.encoding import force_str as force_text
except ImportError:
    from django.utils.encoding import force_text

from django.utils.http import urlsafe_base64_encode
from django.urls import reverse

from ... import registry
from ...base import EmailNotification


class PasswordResetEmail(EmailNotification):
    """
    Email sent when requesting password reset using forgot password feature.
    This replaces django's default email
    """

    template_name = "password_reset"

    def __init__(
        self,
        user,
        site_name=None,
        domain=None,
        extra_email_context=None,
        use_https=False,
        token_generator=default_token_generator,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        html_email_template_name=None,
    ):
        self.to_emails = [user.email]
        self.site_name = site_name
        self.domain = domain
        self.user = user
        self.token_generator = token_generator
        self.use_https = use_https
        self.extra_email_context = extra_email_context
        self.subject_template_name = subject_template_name
        self.email_template_name = email_template_name
        self.html_email_template_name = html_email_template_name

    def get_context_data(self):
        context = super(PasswordResetEmail, self).get_context_data()

        if not self.site_name or self.domain:
            current_site = Site.objects.get_current()
            self.site_name = current_site.name
            self.domain = current_site.domain

        protocol = "https" if self.use_https else "http"
        uid = force_text(urlsafe_base64_encode(force_bytes(self.user.pk)))
        token = self.token_generator.make_token(self.user)

        context.update(
            {
                "full_reset_url": "{}://{}{}".format(
                    protocol,
                    self.domain,
                    reverse(
                        "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
                    ),
                ),
                "email": self.user.email,
                "domain": self.domain,
                "site_name": self.site_name,
                "uid": uid,
                "user": self.user,
                "token": token,
                "protocol": protocol,
                "template_name": self.email_template_name,
                "html_template_name": self.html_email_template_name,
            }
        )

        if self.extra_email_context is not None:
            context.update(self.extra_email_context)

        return context

    def get_subject(self):
        subject = super(PasswordResetEmail, self).get_subject()

        if not subject:
            # subject was not defined on the class. Use the default subject template to get the subject.
            subject = loader.render_to_string(
                self.subject_template_name, self.get_context_data()
            )
            # can't have newlines
            return "".join(subject.splitlines())

        return subject

    @staticmethod
    def get_demo_args():
        User = get_user_model()
        return [User(**{User.USERNAME_FIELD: "username@example.com"})]


registry.register(PasswordResetEmail)
