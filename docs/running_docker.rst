========================
Docker Development Setup
========================

Cloning the project
-------------------

::

    git clone git@github.com:SFDO-Tooling/MetaCI
    cd MetaCI

Docker and Docker-Compose Installation
--------------------------------------

To download and install docker please visit: https://hub.docker.com/?overlay=onboarding 
and follow the installation instructions to download docker if needed.
To verify you have successfully installed docker type:

::
    
    docker -v

*You should see something like the following:*
    ``Docker version 19.03.4, build 9013bf5``


To download and install docker-compose please visit: https://docs.docker.com/v17.09/compose/install/
and follow the installation instructions to download docker-compose if needed.
To verify you have successfully installed docker-compose type:

::

    docker-compose -v

*You should see something like the following:*
    ``docker-compose version 1.16.1, build 6d1ac219``

Running MetaCI In Docker
========================

Below are the following steps necessary to run MetaCI on Docker:

1. Configure MetaCI

   Copy ``.env.example`` to create a file named ``.env`` in the top level of the MetaCI repository.
   Then, follow `<./docs/configuring.rst>`_ to update the variables in this file.

2. `Build Your Docker Containers`_

3. `Run Your Docker Containers`_


Build Your Docker Containers
----------------------------

This next section assumes you have downloaded ``docker`` and ``docker-compose``.
Additionally it assumes you have a ``.env`` file in the root directory of this 
project, a template of variables needed can be found under ``env.example``.

To configure and run your environment you must run 2 commands in the root directory of MetaCI
Note that docker-compose build will take some significant time to build the first time but will
be much faster for subsequent builds. It is also important to note that once you bring 
up the web application it will take roughly 60 seconds to fully compile.
::
    
    docker-compose build

Run Your Docker Containers
--------------------------
MetaCI's docker container comes out of the box with development test
data and the creation of a default admin user.

If you would like to disable this functionality please add a `DJANGO_SETTINGS_MODULE` environment variable
in the web service section of the docker-compose file to set it from its default value (set in Dockerfile) from
`config.settings.dev` to `config.settings.production`.
For examples of how to do this please see `setting docker-compose environment variables`_.

.. _setting docker-compose environment variables: https://docs.docker.com/compose/environment-variables/

Then run the following command:
::

    docker-compose up -d 
    or 
    docker-compose up (for debug mode)

After running this command which will take a couple minutes on startup visit ``localhost:8000/admin/login``
and login with the following credentials if DJANGO_SETTINGS_MODULE is config.settings.dev:

username:
    ``admin``
password:
    ``password``

From here you should be able to run builds. However note that this default account will not be created 
when BUILD_ENV is set to production

Docker Commands
---------------
To stop your virtual containers run the following command:
The docker-compose stop command will stop your containers, but it won’t remove them.
::

    docker-compose stop

To start your virtual containers run the following command:
::

    docker-compose start

To bring your virtual containers up for the first time run the following command:
::

    docker-compose up -d

To bring your virtual containers down run the following command:

.. warning:: The docker-compose down command will stop your containers, 
    but also removes the stopped containers as well as any networks that were created.

::

    docker-compose down
    
Removes stopped service containers. To remove your stopped containers enter the following commands

.. warning:: This will destroy anything that is in the virtual environment, 
    however the database data will persist 

::

    docker-compose rm

(then enter ``y`` when prompted. If you would like to clear the database as well include a -v flag i.e. ``docker-compose down -v``)

To view all running services run the following command:

::
    
    docker-compose ps

If you'd like to test something out manually in that test environment for any reason you can run the following:
In order to run relevant management commands like `manage.py makemigrations`, or if you'd like to test 
something out manually in that test environment for any reason you can run the following:

::

    docker-compose exec web bash

This will drop you into a bash shell running inside your container, where can execute commands.

You can also run commands directly:
::
    
    docker-compose exec web python manage.py makemigrations

Docker development using VS Code
--------------------------------

Because front-end and back-end dependencies are installed in a Docker container
instead of locally, text editors that rely on locally-installed packages (e.g.
for code formatting/linting on save) need access to the running Docker
container. `VS Code`_ supports this using the `Remote Development`_ extension
pack.

Once you have the extension pack installed, when you open the MetaShare folder
in VS Code, you will be prompted to "Reopen in Container". Doing so will
effectively run ``docker-compose up`` and reload your window, now running inside
the Docker container. If you do not see the prompt, run the "Remote-Containers:
Open Folder in Container..." command from the VS Code Command Palette to start
the Docker container.

A number of project-specific VS Code extensions will be automatically installed
for you within the Docker container. See `.devcontainer/devcontainer.json
<.devcontainer/devcontainer.json>`_ and `.devcontainer/docker-compose.dev.yml
<.devcontainer/docker-compose.dev.yml>`_ for Docker-specific VS Code settings.

The first build will take a number of minutes, but subsequent builds will be
significantly faster.

Similarly to the behavior of ``docker-compose up``, VS Code automatically runs
database migrations and starts the development server/watcher. To run any local commands, 
open an `integrated terminal`_ in VS Code (``Ctrl-```) and use any of the development
commands (this terminal runs inside the Docker container and can run all the commands that can be run in
RUNNING.RST and CONTRIBUTING.RST)::

    $ python manage.py migrate  # run database migrations
    $ yarn serve  # start the development server/watcher

For any commands, when using the VS Code integrated terminal inside the
Docker container, omit any ``docker-compose run --rm web...`` prefix, e.g.::

    $ python manage.py promote_superuser <your email>
    $ yarn test:js
    $ python manage.py truncate_data
    $ python manage.py populate_data

``yarn serve`` is run for you on connection to container. You can view the running app at
`<http://localhost:8080/>`_ in your browser.

For more detailed instructions and options, see the `VS Code documentation`_.

.. _VS Code: https://code.visualstudio.com/
.. _Remote Development: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack
.. _integrated terminal: https://code.visualstudio.com/docs/editor/integrated-terminal
.. _VS Code documentation: https://code.visualstudio.com/docs/remote/containers

Environment Variables That Modify The Docker Environment
--------------------------------------------------------

*Note that you very seldom need to change these variables and most have usable defaults.*

CHROMEDRIVER_DIR:
    This environment variable represents the directory where the chromedriver package resides
    in the filesystem. CHROMEDRIVER_DIR is set for you in the Dockerfile.

NODE_VERSION: 
    Environment variable used to set node version for download, defaults to the version set in the engines.node field of package.json.

YARN_VERSION: 
    Environment variable used to set yarn version for download, defaults to the version set in the engines.yarn field of package.json.

PYTHONUNBUFFERED: 
    Environment variable set in Dockerfile used to not write .pyc files to Docker container
       
DATABASE_URL:
    Environment variable set in Dockerfile. Represents the full path of database url.

REDIS_URL: 
    This represents the url to the location where the redis server, configured for Meta CI. Set in Dockerfile.

DJANGO_HASHID_SALT: 
    This represents the hashid salt for the django application, currently set to 
    arbritary string due to non production defaults, can be overridden 
    in docker-compose.yml. Currently set in Dockerfile.
    
Build Arguments
-------------------------------

BUILD_ENV:
    Argument used to determine what dependencies and scripts to run when installing
    dependencies, populating databases, and setting ``DJANGO_SETTINGS_MODULE``. Values:
    ``dev``, ``production``, and ``test``.

CHROMEDRIVER_VERSION:
    Argument used to override the version of Chromedriver to install, which defaults to
    the Chromedriver version returned by ``https://chromedriver.storage.googleapis.com/LATEST_RELEASE_X``
    (where ``X`` is the version number of the installed Chrome version).
