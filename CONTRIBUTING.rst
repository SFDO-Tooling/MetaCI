=================
Developing MetaCI
=================

MetaCI can be setup using either docker virtual containers
or on your local machine. 
 
Using Docker
============

To set up MetaCI using docker please
see the following instructions `<./docs/running_docker.rst>`_.


Using Local Machine
===================

As mentioned above, MetaCI can be configured locally. 
To achieve this follow the instructions provided in `<./docs/running.rst>`_.

Running the Server
==================
Docker runs the server automatically. If you are not using Docker for 
development, you can run it like this:

- ``make start``: starts development server (with watcher) at
  `<http://localhost:8080/>`_ (assets are served from ``dist/`` dir)

Development Tasks
=================

To run these tests with docker first run the following commands, 

::

    docker-compose up -d
    docker-compose exec web bash

If you are not using docker or are using the VS Code integrated terminal 
inside the Docker container simply execute the commands in your project's 
root directory:

- ``pytest``: run Python tests

Commits
=======

In commit messages or pull request titles, we use the following emojis to label
which development commands need to be run before serving locally (these are
automatically prepended to commit messages):

- 📦 (``:package:``) -> ``pip install -r requirements/local.txt``
- 🛢 (``:oil_drum:``) -> ``python manage.py migrate``
- 🐈 (``:cat2:``) -> ``yarn``

Internationalization
====================

To build and compile ``.mo`` and ``.po`` files for the backend, run::

   $ python manage.py makemessages --locale <locale>
   $ python manage.py compilemessages

These commands require the `GNU gettext toolset`_ (``brew install gettext``).

.. _GNU gettext toolset: https://www.gnu.org/software/gettext/
.. _user language is auto-detected at runtime: https://github.com/i18next/i18next-browser-languageDetector

Developing with SLDS
====================

MetaCI uses https://github.com/SalesforceFoundation/django-slds which imports version 2.1.2 of the Salesforce Lightning Design System.

You can find a CSS and component reference archived here: https://archive-2_1_2.lightningdesignsystem.com/
