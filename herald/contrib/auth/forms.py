"""
Form classes to be used with django.contrib.auth
"""

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

from .notifications import PasswordResetEmail


class HeraldPasswordResetForm(PasswordResetForm):
    """
    Form used when entering your email to send a password reset email
    """

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """

        email = self.cleaned_data["email"]
        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override

            PasswordResetEmail(
                user,
                site_name=site_name,
                domain=domain,
                extra_email_context=extra_email_context,
                use_https=use_https,
                token_generator=token_generator,
                subject_template_name=subject_template_name,
                email_template_name=email_template_name,
                html_email_template_name=html_email_template_name,
            ).send()
