"""
Urls for herald app
"""

try:
    from django.urls import re_path as url
except ImportError:
    from django.conf.urls import url

from .views import TestNotificationList, TestNotification

urlpatterns = [
    url(r'^$', TestNotificationList.as_view(), name='herald_preview_list'),
    url(r'^(?P<index>\d+)/(?P<type>[\w\-]+)/$', TestNotification.as_view(), name='herald_preview'),
]
