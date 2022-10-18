"""
Views for testing notifications. Should not be present in production
"""
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import TemplateView, View

from . import registry


class TestNotificationList(TemplateView):
    """
    View for listing out all notifications with links to view rendered versions of them
    """

    template_name = "herald/test/notification_list.html"

    def get_context_data(self, **kwargs):
        context = super(TestNotificationList, self).get_context_data(**kwargs)

        context["notifications"] = [
            (index, x.__name__, x.render_types, (y.__name__ for y in x.__bases__))
            for index, x in enumerate(registry._registry)  # pylint: disable=W0212
        ]

        return context


class TestNotification(View):
    """
    View for showing rendered test notification
    """

    def get(self, request, *args, **kwargs):  # pylint: disable=W0613
        """
        GET request
        """

        index = int(kwargs["index"])
        render_type = kwargs["type"]

        obj = registry._registry[index](
            *registry._registry[index].get_demo_args()
        )  # pylint: disable=W0212

        context = obj.get_context_data()

        content = obj.render(render_type, context)

        render_type = "plain" if render_type == "text" else render_type
        charset = settings.DEFAULT_CHARSET

        return HttpResponse(
            content, content_type="text/{}; charset={}".format(render_type, charset)
        )
