"""
Base notification classes
"""

import json
from email.mime.base import MIMEBase
from mimetypes import guess_type

import jsonpickle
import six

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.files import File

from .models import SentNotification


class NotificationBase(object):
    """
    base class for sending notifications
    """

    render_types = []
    template_name = None
    context = None
    user = None
    can_disable = True
    verbose_name = None

    def get_context_data(self):
        """
        :return: the context data for rendering the email or text template
        """

        context = self.context or {}

        if settings.DEBUG:
            context['base_url'] = ''
        else:
            site = Site.objects.get_current()
            context['base_url'] = 'http://' + site.domain

        return context

    def send(self, raise_exception=False, user=None):
        """
        Handles the preparing the notification for sending. Called to trigger the send from code.
        If raise_exception is True, it will raise any exceptions rather than simply logging them.
        returns boolean whether or not the notification was sent successfully
        """
        context = self.get_context_data()

        recipients = self.get_recipients()

        if 'text' in self.render_types:
            text_content = self.render('text', context)
        else:
            text_content = None

        if 'html' in self.render_types:
            html_content = self.render('html', context)
        else:
            html_content = None

        sent_from = self.get_sent_from()
        subject = self.get_subject()
        extra_data = self.get_extra_data()

        sent_notification = SentNotification(
            recipients=','.join(recipients),
            text_content=text_content,
            html_content=html_content,
            sent_from=sent_from,
            subject=subject,
            extra_data=json.dumps(extra_data) if extra_data else None,
            notification_class='{}.{}'.format(self.__class__.__module__, self.__class__.__name__),
            attachments=self._get_encoded_attachments(),
            user=user,
        )

        return self.resend(sent_notification, raise_exception=raise_exception)

    def _get_encoded_attachments(self):
        attachments = self.get_attachments()

        if attachments:
            new_attachments = []

            for attachment in attachments:
                if isinstance(attachment, File):
                    attachment.seek(0)
                    new_attachments.append((attachment.name, attachment.read(), guess_type(attachment.name)[0]))
                else:
                    new_attachments.append(attachment)

            attachments = new_attachments

        return jsonpickle.dumps(attachments)

    def get_recipients(self):
        """
        Returns a list of recipients. However the subclass defines that. (emails, phone numbers, etc)
        """

        raise NotImplementedError('Must implement get_recipients.')

    def get_extra_data(self):
        """
        Returns a dictionary of extra data to be stored, and used for sending.
        MUST BE JSON SERIALIZABLE
        """

        return {}

    def get_sent_from(self):
        """
        Returns a "sent from" string. However the subclass defines that. (email, phone number, etc)
        """

        raise NotImplementedError('Must implement get_recipients.')

    def get_subject(self):
        """
        Returns a subject string. Optional.
        """

        return None

    def get_attachments(self):
        """
        Return a list of attachments or None.

        This only works with email.
        """
        return None

    def render(self, render_type, context):
        """
        Renders the template

        :param render_type: the content type to render
        :param context: context data dictionary
        :return: the rendered content
        """

        assert render_type in self.render_types, 'Invalid Render Type'

        try:
            content = render_to_string('herald/{}/{}.{}'.format(
                render_type,
                self.template_name,
                'txt' if render_type == 'text' else render_type
            ), context)
        except TemplateDoesNotExist:
            content = None
            if settings.DEBUG:
                raise

        return content

    @staticmethod
    def get_demo_args():
        """
        Returns iterable of arguments needed to initialize notification for demo purposes
        Usually you want to generate dummy data here for testing
        """
        return []

    @classmethod
    def resend(cls, sent_notification, raise_exception=False):
        """
        Takes a saved sent_notification and sends it again.
        returns boolean whether or not the notification was sent successfully
        """

        # handle skipping a notification based on user preference
        if hasattr(sent_notification.user, 'usernotification'):
            notifications = sent_notification.user.usernotification
            if notifications.disabled_notifications.filter(notification_class=cls.__name__).exists():
                sent_notification.date_sent = timezone.now()
                sent_notification.status = sent_notification.STATUS_USER_DISABLED
                sent_notification.save()
                return True

        try:
            cls._send(
                sent_notification.get_recipients(),
                sent_notification.text_content,
                sent_notification.html_content,
                sent_notification.sent_from,
                sent_notification.subject,
                sent_notification.get_extra_data(),
                sent_notification.get_attachments(),
            )
            sent_notification.status = sent_notification.STATUS_SUCCESS
        except Exception as exc:  # pylint: disable=W0703
            # we want to handle any exception whatsoever
            sent_notification.status = sent_notification.STATUS_FAILED
            sent_notification.error_message = six.text_type(exc)

            if raise_exception:
                raise exc

        sent_notification.date_sent = timezone.now()
        sent_notification.save()

        return sent_notification.status == sent_notification.STATUS_SUCCESS

    @staticmethod
    def _send(recipients, text_content=None, html_content=None, sent_from=None, subject=None, extra_data=None,
              attachments=None):
        """
        Handles the actual sending of the notification. Sub classes must override this
        """

        raise NotImplementedError('Must implement send.')


class EmailNotification(NotificationBase):
    """
    Base class for email notifications
    """

    render_types = ['text', 'html']
    from_email = None
    subject = None
    to_emails = None
    bcc = None
    cc = None  # pylint: disable=C0103
    headers = None
    reply_to = None
    attachments = None

    def get_context_data(self):
        context = super(EmailNotification, self).get_context_data()
        context['subject'] = self.subject
        return context

    def get_recipients(self):
        return self.to_emails

    def get_sent_from(self):
        from_email = self.from_email
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        return from_email

    def get_subject(self):
        return self.subject

    def get_extra_data(self):
        extra_data = {}

        if self.bcc:
            extra_data['bcc'] = self.bcc

        if self.cc:
            extra_data['cc'] = self.cc

        if self.headers:
            extra_data['headers'] = self.headers

        if self.reply_to:
            extra_data['reply_to'] = self.reply_to

        return extra_data

    def get_attachments(self):
        """
        Return a list of attachments or None.

        This only works with email.
        """
        return self.attachments

    @staticmethod
    def _send(recipients, text_content=None, html_content=None, sent_from=None, subject=None, extra_data=None,
              attachments=None):
        if extra_data is None:
            extra_data = {}

        mail = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=sent_from,
            to=recipients,
            bcc=extra_data.get('bcc', None),
            headers=extra_data.get('headers', None),
            cc=extra_data.get('cc', None),
            reply_to=extra_data.get('reply_to', None),
        )

        if html_content:
            mail.attach_alternative(html_content, 'text/html')

        for attachment in (attachments or []):
            # All mimebase attachments must have a Content-ID or Content-Disposition header
            # or they will show up as unnamed attachments"
            if isinstance(attachment, MIMEBase):
                if attachment.get('Content-ID', False):
                    # if you are sending attachment with content id,
                    # subtype must be 'related'.
                    mail.mixed_subtype = 'related'

                mail.attach(attachment)
            else:
                mail.attach(*attachment)

        mail.send()


class TwilioTextNotification(NotificationBase):
    """
    Base class for text notifications.
    Uses twilio
    """

    render_types = ['text']
    from_number = None
    to_number = None

    def get_recipients(self):
        return [self.to_number]

    def get_sent_from(self):
        from_number = self.from_number
        if not from_number:
            try:
                from_number = settings.TWILIO_DEFAULT_FROM_NUMBER
            except AttributeError:
                raise Exception(
                    'TWILIO_DEFAULT_FROM_NUMBER setting is required for sending a TwilioTextNotification'
                )

        return from_number

    @staticmethod
    def _send(recipients, text_content=None, html_content=None, sent_from=None, subject=None, extra_data=None,
              attachments=None):
        try:
            # twilio version 6
            from twilio.rest import Client
        except ImportError:
            try:
                # twillio version < 6
                from twilio.rest import TwilioRestClient as Client
            except ImportError:
                raise Exception('Twilio is required for sending a TwilioTextNotification.')

        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
        except AttributeError:
            raise Exception(
                'TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN settings are required for sending a TwilioTextNotification'
            )

        client = Client(account_sid, auth_token)

        client.messages.create(
            body=text_content,
            to=recipients[0],
            from_=sent_from
        )
