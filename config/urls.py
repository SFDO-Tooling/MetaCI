from django.conf import settings
from django.urls import re_path
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views
from django.views.generic import TemplateView

from metaci import views as mbci_views
from metaci.build import views as build_views
from metaci.repository.views import github_webhook

urlpatterns = [
    re_path(
        r"^robots\.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    re_path(r"^$", build_views.build_list, name="home"),
    re_path(
        r"^about/$",
        mbci_views.AboutView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {%  url 'admin:index' %}
    re_path(settings.ADMIN_URL_ROUTE, admin.site.urls),
    # User management
    re_path(r"^users/", include("metaci.users.urls", namespace="users")),
    re_path(r"^accounts/", include("allauth.urls")),
    # django-rq
    re_path(r"^django-rq/", include("django_rq.urls")),
    # search
    re_path(r"^search$", build_views.build_search, name="search"),
    re_path(r"^api/", include("metaci.api.urls")),
    re_path(r"^builds/", include("metaci.build.urls")),
    re_path(r"^cohorts/", include("metaci.release.urls")),
    re_path(r"^create-org/", include("metaci.create_org.urls")),
    re_path(r"^notifications/", include("metaci.notification.urls")),
    re_path(r"^tests/", include("metaci.testresults.urls")),
    re_path(r"^plans/", include("metaci.plan.urls")),
    re_path(r"^orgs/", include("metaci.cumulusci.urls")),
    re_path(r"^hirefire/", include("metaci.hirefire.urls")),
    re_path(r"^repos/", include("metaci.repository.urls")),
    re_path(r"^webhook/github/push$", github_webhook, name="github_webhook"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# override default error view
handler403 = "metaci.views.custom_403"

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these paths in the browser to see how these error pages look.
    urlpatterns += [
        re_path(
            r"^400/$",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        re_path(
            r"^403/$",
            mbci_views.custom_403,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        re_path(
            r"^404/$",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        re_path(r"^500/$", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [re_path(r"^__debug__/", include(debug_toolbar.urls))]
