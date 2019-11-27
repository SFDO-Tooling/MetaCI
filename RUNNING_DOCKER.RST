Development Setup
=================

Cloning the project
-------------------

::

    git clone git@github.com:SFDO-Tooling/MetaCI
    cd MetaCI

Docker and Docker-Compose Installation:
--------------------------------------
To download and install docker please visit: https://hub.docker.com/?overlay=onboarding 
and follow the installation instructions to download docker if needed: 

To verify you have successfully installed docker type:

::
    
    docker -v

You should see something like the following:


To download and install docker-compose please visit: https://docs.docker.com/v17.09/compose/install/
and follow the installation instructions to download docker-compose if needed:
To verify you have successfully installed docker type:

::

    docker-compose -v

You should see something like the following):

``docker-compose version 1.16.1, build 6d1ac219``


Running MetaCI In Docker:
=========================

To run MetaCI on Docker there are 3 major steps necessary:
----------------------------------------------------------

- `.env File Creation and Variable Declaration`_
.. _.env File Creation and Variable Declaration: https://github.com/SFDO-Tooling/MetaCI/blob/feature/docker/CONTRIBUTING.rst#env-file-creation-and-variable-declaration

- `Building Your Docker Containers`_
.. _Building Your Docker Containers: https://github.com/SFDO-Tooling/MetaCI/blob/feature/docker/CONTRIBUTING.rst#building-your-docker-containers

- `Running Your Docker Containers`_
.. _Running Your Docker Containers: https://github.com/SFDO-Tooling/MetaCI/blob/feature/docker/CONTRIBUTING.rst#running-your-docker-containers


.env File Creation and Variable Declaration
-------------------------------------------

*Please begin by making a copy of env.example and renaming it .env in your root project directory*

*WHERE TO GET EACH VARIABLE and FORMAT NEEDED*
(REQUIRED TO RUN LOCALLY, bare minimum)

DJANGO_SECRET_KEY: 
    This represents the secret key for the django web application, for local testing, arbritary strings such as the one given in the env.example will suffice. Otherwise use your production secret key.

GITHUB_USERNAME:     
    This represents the username of either the tester or service account configured for MetaCI

GITHUB_PASSWORD:      
    This represents the password or personal access token a user must have to access their account a personal access token will be used when Multi Factor Authentication is enabled.

If you need to generate a personal access token please visit the following: https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

SFDX_CLIENT_ID:       
    This tells sfdx the client id of the connected app to use for connecting to the Dev Hub to create scratch orgs (so it's only needed for running plans that use a scratch org). For SFDO staff it's easiest to use an existing connected app, so its best to ask another team member. External users setting up MetaCI will need to create their own connected app, which they can do in the Dev Hub org. You can adapt these instructions https://cumulusci.readthedocs.io/en/latest/tutorial.html#creating-manually but there is a difference for MetaCI: because it's connecting to the org non-interactively, the connected app needs to be set up to use the JWT oauth flow. That means when creating the connected app the user needs to check the "Use Digital Signatures" box and upload a certificate. If you are a member of SFDO please visit the following quip link https://salesforce.quip.com/sm9bA3R6GwiK, and look under section 5 of SFDX Command Line Tool Setup & Install

SFDX_HUB_KEY:          
    SFDX_HUB_KEY is the private key that was used to create the certificate. Shared through last pass. In the form of a pem key. Called `SFDX Hub Org Key` n Release Engineering folder.
    
FORMATTING SFDX_HUB_KEY in .env
    IMPORTANT to format on a single line, escaping each newline in the key with ``\n`` character otherwise the variable will not be read correctly. Must look like the following example and CANNOT BE IN QUOTES:

::

    SFDX_HUB_KEY=-----BEGIN RSA PRIVATE KEY-----\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nv4fU8l7TeYVQVvSdWJmN3sBZ4bnG3GSu1u6viGQwxulxtJrLnclEgL2Tq0npRn/x\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nDMG9uoYPD4X0rkKz/4PI2jcO4NgkWfTiQY0yEDQNM31Sfcw5lNSeKHrrnG7fHx3q\nu9fb7GxWMi74LBlMVlseREzfYRyUI7ukPZNgdvAGbp3TI0ITAQTbTzKPR4FdyZbm\nysuDXZuQpbifXxBKPVVYHxbdEYkabK4FKeB1cNRI72T0jt+r6DqFTjfpJHs/FjEo\nq86HWtHWGh1AYaIi5LBMLQ1tNEcSNvvZW49AsUISqJRFwFvwubBhLh36DaucM4aI\nWPLQUeUCgYEA37+Qy6o3vvfwj0pJ4Ecqo5FRZkxBbUmVTdr1RVPAFxRchsKzsvx4\nWKRDkmIlvf/vpaB4cUsYDZVOd1qGXciFQODk+FfLbOCDbcR1qv87YL/tKNRO/sox\nBt3yS6vyCokn48Ycaqs+tYcHC2O0Vaye/VvwwUSQMLLVdGR84N2hzX8CgYEA3S15\ndqEiWI8a27EX4AD4q9avNJJCwkO5B9/YBnZBpy1DcFSozP5JfgoH1ilK4tmiXjZO\n3Y+oTcKRUKOSQPjv8obTt3N3xtdabWMW6sH31kOfiKOmDg2lw/UjYQ+xO5FBE/Pi\nOR4XRbhSe04dJ+U2Gik38f/WtgA9h53YOeAJ5UMCgYA2kFLRN+tsSK6DYwxtAy3k\nwZVmKwZxjlY4rELP60KW3kJKIsULywHWLAjGc+TcVsOsUlvM1RFCjryZ4puN106X\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nMINDSJIBAAAFDVCXwVAe1YBRi+WpkTp02mOPbgj9NgjpwKQEOJugAqdzBdprBxTs\nDtfenYxFW9Iqj58oCzDuUJGWkA4lolYMkcbvEhE2fhOTNH9UdFyhC6WDQuaFnr1x\nbC4LAoGAbzqfS4vF+kloxneGdWJnAiibvEEUWVmMZ4GMF0a7w0x2l+jwiGT2Kt8P\nC5VdZvMMktzfTHynq6j6BfnSYCBJFNp1EbwZksGtEnT4ggCdIVNY+N1wVeok1vp/\n17/R87a1O62MeA5gBeGdpoMof/XrFVUdb/kSXyNt8miUeLOez/M=\n-----END RSA PRIVATE KEY-----


SFDX_HUB_USERNAME: 
    This represents the username used to login to your sfdx hub account

CONNECTED_APP_CLIENT_ID:
    This represents the client id of the packaging org that MetaCI is running builds on

CONNECTED_APP_CLIENT_SECRET: 
    This represents the secret of the packaging org configured for MetaCI

CONNECTED_APP_CALLBACK_URL:
    This represents the packaging org's callback url 

To acquire the connected_app variables if you are already properly configured with cci:

::
    
    cci service info connected_app

You should be able to now record all three variables.

If you have not set up a connected app please visit the following to achieve this.
https://cumulusci.readthedocs.io/en/latest/tutorial.html#creating-a-connected-app
Once done, confirm with the aformentioned command to ensure you are properly configured 
with regards to the connected_app variables.

(REQUIRED FOR PRODUCTION include REQUIRED LOCAL VARIABLES as well for PRODUCTION)
    - GITHUB_WEBHOOK_SECRET
    - DJANGO_AWS_ACCESS_KEY_ID
    - DJANGO_AWS_SECRET_ACCESS_KEY
    - DJANGO_AWS_STORAGE_BUCKET_NAME
    - DJANGO_SERVER_EMAIL
    - DJANGO_SENTRY_DSN

(OTHER VARIABLES SET BY DEFAULT FOR YOU)

BUILD_ENV: 
    Environment variable used to determine what dependencies and scripts to run when installing dependencies and populating databases, currently set in docker-compose.yml web service environment variable

NODE_VERSION: 
    Environment variable used to set node version for download, this variable is set in the Dockerfile

YARN_VERSION: 
    Environment variable used to set yarn version for download, this variable is set in the Dockerfile

PYTHONUNBUFFERED: 
    Environment variable set in Dockerfile used to not write .pyc files to Docker container

POSTGRES_USER: 
    Environment variable set in the docker-compose.yml file under the postgres service, represents database user. This value has already been configured for you unless you decide to reconfigure it.

POSTGRES_PASSWORD: 
    Environment variable set in the docker-compose.yml file under the postgres service, represents database password.This database is configured with no password for development purposes so leave as is unless changing for production purposes.

POSTGRES_DB:
    Environment variable set in the docker-compose.yml file under the postgres service, represents database. This variable has already been set to the proper value `metaci` for the user.
       
DATABASE_URL:
    Environment variable set in Dockerfile. Represents the full path of database url.

REDIS_URL: 
    This represents the url to the location where the redis server, configured for Meta CI. Set in Dockerfile.

DJANGO_HASHID_SALT: 
    This represents the hashid salt for the django application, currently set to arbritary string due to non production defaults, can be overridden in docker-compose.yml. Currently set in Dockerfile.

DJANGO_SECRET_KEY: 
    This represents the key for the django application, currently set to arbritary string due to non production defaults, can be overridden in docker-compose.yml. Currently set in Dockerfile.

Building Your Docker Containers:
-------------------------------

This next section assumes you have downloaded ``docker`` and ``docker-compose``.
Additionally it assumes you have a ``.env`` file in the root directory of this 
project, a template of variables needed can be found under ``env.example``.

To configure and run your environment you must run 2 commands in the root directory of MetaCI
Note that docker-compose build will take some significant time to build the first time but will
be much faster for subsequent builds. It is also important to note that once you bring up the web application
it will take roughly 60 seconds to fully compile. 

::
    
    docker-compose build

Running Your Docker Containers:
-------------------------------
::

    docker-compose up -d 
    or 
    docker-compose up (for debug mode)

If you would like to populate your instance of MetaCI with test data simply set the BUILD_ENV variable to development.
After that visit ``localhost:8000/admin/login`` and login with the credentials

username
::

    admin
password
::

    password

From here you should be able to run builds. However note that this default account will not be created 
when BUILD_ENV is set to production

To bring your virtual containers down run the following command:
        
::

    docker-compose down
    
To destroy your container enter the following commands:
* Note this will destroy anything that is in the virtual environment, however the database data will persist *
::

    docker-compose down
    docker-compose down
(yes this was written twice intentionally)

To view all running services run the following command:

::
    
    docker-compose ps

If you'd like to test something out manually in that test environment for any reason you can run the following:
    
::

    docker-compose exec web bash

After this you will be inside of a linux commandline, and are free to test around in your container.
