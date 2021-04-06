from allauth.socialaccount.providers.github.provider import GitHubProvider


class CustomGitHubProvider(GitHubProvider):
    package = "metaci.oauth2.github"


provider_classes = [CustomGitHubProvider]
