from __future__ import absolute_import
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.urls import re_path, include


urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path('^', include(auth_urls)),
    re_path(r'^herald/', include('herald.urls')),
]
