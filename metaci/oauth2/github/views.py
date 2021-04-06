from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)


def ensure_socialapp_in_db(token):
    """Make sure that token is attached to a SocialApp in the db.

    Since we are using SocialApps constructed from settings,
    there are none in the db for tokens to be related to
    unless we create them here.
    """
    if token.app.pk is None:
        provider = providers.registry.by_id(token.app.provider)
        app, created = SocialApp.objects.get_or_create(
            provider=provider.id,
            name=provider.name,
            client_id="-",
        )
        token.app = app


class CustomGitHubOauth2Adapter(GitHubOAuth2Adapter):
    """GitHub adapter that can handle the app being configured in settings"""

    def complete_login(self, request, app, token, **kwargs):
        # make sure token is attached to a SocialApp in the db
        ensure_socialapp_in_db(token)
        return super().complete_login(request, app, token, **kwargs)


oauth2_login = OAuth2LoginView.adapter_view(CustomGitHubOauth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(CustomGitHubOauth2Adapter)
