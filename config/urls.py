# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views
from django.views.generic import TemplateView

from metaci import views as mbci_views
from metaci.build import views as build_views
from metaci.repository.views import github_webhook

urlpatterns = [
    url(
        r"^robots\.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    url(r"^$", build_views.build_list, name="home"),
    url(
        r"^about/$",
        mbci_views.AboutView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL_ROUTE, admin.site.urls),
    # User management
    url(r"^users/", include("metaci.users.urls", namespace="users")),
    url(r"^accounts/", include("allauth.urls")),
    # django-rq
    url(r"^django-rq/", include("django_rq.urls")),
    # search
    url(r"^search$", build_views.build_search, name="search"),
    url(r"^api/", include("metaci.api.urls")),
    url(r"^builds/", include("metaci.build.urls")),
    url(r"^create-org/", include("metaci.create_org.urls")),
    url(r"^notifications/", include("metaci.notification.urls")),
    url(r"^tests/", include("metaci.testresults.urls")),
    url(r"^plans/", include("metaci.plan.urls")),
    url(r"^orgs/", include("metaci.cumulusci.urls")),
    url(r"^hirefire/", include("metaci.hirefire.urls")),
    url(r"^repos/", include("metaci.repository.urls")),
    url(r"^webhook/github/push$", github_webhook, name="github_webhook"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(
            r"^400/$",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        url(
            r"^403/$",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        url(
            r"^404/$",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        url(r"^500/$", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [url(r"^__debug__/", include(debug_toolbar.urls))]
