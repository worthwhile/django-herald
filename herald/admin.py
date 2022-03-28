"""
Admin for notifications
"""

from functools import update_wrapper

try:
    from django.urls import re_path as url
except ImportError:
    from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.utils import unquote
from django.utils.safestring import mark_safe
from django.urls import reverse

from .models import SentNotification, Notification


@admin.register(SentNotification)
class SentNotificationAdmin(admin.ModelAdmin):
    """
    Admin for viewing historical notifications sent
    """

    list_display = ('notification_class', 'recipients', 'subject', 'date_sent', 'status')
    list_filter = ('status', 'notification_class')
    date_hierarchy = 'date_sent'
    readonly_fields = ('resend', )
    search_fields = ('recipients', 'subject', 'text_content', 'html_content', 'sent_from')
    autocomplete_fields = ('user', )

    def resend(self, obj):
        """
        Creates a link field that takes user to re-send view to resend the notification
        """

        opts = self.model._meta  # pylint: disable=W0212
        resend_url = reverse(
            'admin:%s_%s_resend' % (opts.app_label, opts.model_name),
            current_app=self.admin_site.name,
            args=(obj.pk, )
        )

        return mark_safe('<a href="{}">Resend</a>'.format(resend_url))

    def get_urls(self):
        urls = super(SentNotificationAdmin, self).get_urls()
        opts = self.model._meta  # pylint: disable=W0212

        def wrap(view):
            """
            Copied from super class
            """
            def wrapper(*args, **kwargs):
                """
                Copied from super class
                """
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = opts.app_label, opts.model_name

        return [
            url(r'^(.+)/resend/$', wrap(self.resend_view), name='%s_%s_resend' % info),
        ] + urls

    @csrf_protect_m
    def resend_view(self, request, object_id, extra_context=None):  # pylint: disable=W0613
        """
        View that re-sends the notification
        """

        obj = self.get_object(request, unquote(object_id))

        success = obj.resend()

        if success:
            self.message_user(request, 'The notification was resent successfully.', messages.SUCCESS)
        else:
            self.message_user(request, 'The notification failed to resend.', messages.ERROR)

        return self.response_post_save_change(request, obj)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin for viewing/managing notifications in the system
    """
    list_display = ('notification_class', 'verbose_name', 'can_disable')
    search_fields = ('notification_class', 'verbose_name')

