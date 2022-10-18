from __future__ import absolute_import
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.urls import include

try:
    from django.urls import re_path as url
except ImportError:
    from django.conf.urls import url


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url("^", include(auth_urls)),
    url(r"^herald/", include("herald.urls")),
]
