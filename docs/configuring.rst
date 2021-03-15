==================
Configuring MetaCI
==================


.env File Creation And Variable Declaration
-------------------------------------------

*Please begin by making a copy of env.example and renaming it .env in your root project directory*

Local Variables
---------------

DJANGO_SECRET_KEY: 
    This represents the secret key used to sign session cookies for the Django web application.
    Set it to an arbitrary string that is not shared with another Django site.

POSTGRES_USER:
    Environment variable set in ``.env``, representing the database username.
    This value defaults to ``metaci``.

POSTGRES_PASSWORD: 
    Environment variable set in ``.env``, representing the database password.

POSTGRES_DB:
    Environment variable set in ``.env``, representing the database name.
    This value defaults to ``metaci``.

DATABASE_URL:
    Used by Django to connect to PostgreSQL. Edit it to make sure the password matches POSTGRES_PASSWORD.

MetaCI must authenticate with the GitHub API to fetch repositories and create releases. 
This can be set up for a GitHub user by setting GITHUB_USERNAME and GITHUB_PASSWORD, 
or for a GitHub App by setting GITHUB_APP_ID and GITHUB_APP_KEY.

GITHUB_USERNAME:     
    This represents the username of either the tester or service account configured for MetaCI

GITHUB_PASSWORD:      
    This represents the password or personal access token a user must have to access 
    their account. A `personal access token` will be used when Multi Factor Authentication is enabled.

OR

GITHUB_APP_ID:
    This represents the app id of your github app allowing you to authenticate your machine
    with github.

GITHUB_APP_KEY:
    This represents the private key used for authentication for github applications.

If you need to generate a personal access token please visit `Github's documentation`_:

.. _Github's documentation: https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

SFDX_CLIENT_ID:       
    This tells sfdx the client id of the connected app to use for connecting to 
    the Dev Hub to create scratch orgs (so it's only needed for running plans that use a scratch org).
    If you are a member of SFDO please reach out to Release Engineering for help acquiring the proper SFDX_CLIENT_ID. 
    For SFDO release engineering staff it's easiest to use an existing connected app, so its best to ask another team member. 
    External users setting up MetaCI will need to create their own connected app, 
    which they can do in the Dev Hub org. 
    You can adapt these instructions https://cumulusci.readthedocs.io/en/latest/tutorial.html#creating-manually 
    but there is a difference for MetaCI: because it's connecting to the org non-interactively, 
    the connected app needs to be set up to use the JWT oauth flow. 
    That means when creating the connected app the user needs to check the "Use Digital Signatures" 
    box and upload a certificate. 

SFDX_HUB_KEY:          
    SFDX_HUB_KEY is the private key that was used to create the certificate.
    Shared through last pass. In the form of a pem key. 
    
    In .env, important to format on a single line, representing any newlines in the key as ``\n``
    otherwise the variable will not be read correctly.

SFDX_HUB_USERNAME: 
    This represents the username used to login to your sfdx hub account

CONNECTED_APP_CLIENT_ID:
    This represents the client id of the connected app that MetaCI will use for authenticating to any persistent org. 
    It's fine to use the same connected app that is being used for SFDX_CLIENT_ID and SFDX_HUB_KEY.

CONNECTED_APP_CLIENT_SECRET: 
    This represents the secret of the connected app configured for MetaCI

CONNECTED_APP_CALLBACK_URL:
    This represents the connected app's callback url 

To acquire the connected_app variables just use the client id, client secret and callback url 
of the connected app that was created for ``SFDX_CLIENT_ID`` and ``SFDX_HUB_KEY``.

Some rough tests of whether these variables are set can be done using this
command:

    $ python manage.py verify_environment

There are limits to how much validation can be done, however.
