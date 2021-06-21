from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import CustomGitHubProvider

urlpatterns = default_urlpatterns(CustomGitHubProvider)
