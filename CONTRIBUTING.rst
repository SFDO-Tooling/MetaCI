=================
Developing MetaCI
=================

MetaCI can be setup using either docker virtual containers
or on your local machine. 
 
Using Docker
============

To set up MetaCI using docker please
see the following instructions `<./docs/RUNNING_DOCKER.rst>`_.


Using Local Machine
===================

As mentioned above, MetaCI can be configured locally. 
To achieve this follow the instructions provided in `<./docs/RUNNING.rst>`_.

Development Tasks
=================

To run these tests with docker first run the following commands, if you are not using docker,
simply execute the commands in your project's root directory:

::

    docker-compose up -d
    docker-compose exec web bash


- ``yarn serve``: starts development server (with watcher) at
  `<http://localhost:8080/>`_ (assets are served from ``dist/`` dir)
- ``yarn pytest``: run Python tests
- ``yarn test``: run JS tests
- ``yarn test:watch``: run JS tests with a watcher for development
- ``yarn lint``: formats and lints ``.scss`` and ``.js`` files; lints ``.py``
  files
- ``yarn prettier``: formats ``.scss`` and ``.js`` files
- ``yarn eslint``: lints ``.js`` files
- ``yarn flow``: runs JS type-checking
- ``yarn stylelint``: lints ``.scss`` files
- ``yarn flake8``: lints ``.py`` files
- ``yarn build``: builds development (unminified) static assets into ``dist/``
  dir
- ``yarn prod``: builds production (minified) static assets into ``dist/prod/``
  dir

In commit messages or pull request titles, we use the following emojis to label
which development commands need to be run before serving locally (these are
automatically prepended to commit messages):

- 📦 (``:package:``) -> ``pip install -r requirements/local.txt``
- 🛢 (``:oil_drum:``) -> ``python manage.py migrate``
- 🐈 (``:cat2:``) -> ``yarn``
- 🙀 (``:scream_cat:``) -> ``rm -rf node_modules/; bin/unpack-node; yarn``

Internationalization
====================

To build and compile ``.mo`` and ``.po`` files for the backend, run::

   $ python manage.py makemessages --locale <locale>
   $ python manage.py compilemessages

These commands require the `GNU gettext toolset`_ (``brew install gettext``).

For the front-end, translation JSON files are served from
``locales/<language>/`` directories, and the `user language is auto-detected at
runtime`_.

During development, strings are parsed automatically from the JS, and an English
translation file is auto-generated to ``locales_dev/en/translation.json`` on
every build (``yarn build`` or ``yarn serve``). When this file changes,
translations must be copied over to the ``locales/en/translation.json`` file in
order to have any effect.

Strings with dynamic content (i.e. known only at runtime) cannot be
automatically parsed, but will log errors while the app is running if they're
missing from the served translation files. To resolve, add the missing key:value
translations to ``locales/<language>/translation.json``.

.. _GNU gettext toolset: https://www.gnu.org/software/gettext/
.. _user language is auto-detected at runtime: https://github.com/i18next/i18next-browser-languageDetector

Type Checking
=============
We use "flow_" for type-checking for the time being. You should be able to just
type "flow" to validate that there are no known type errors.

If you need to use libraries that do not have flow definitions, you could edit
a file with a name like ``flow-typed/npm/@package/module_vx.x.x.js`` to stub out addition component
type definitions. OR you can run ``flow-typed update --ignoreDeps dev`` to allow
it to automatically generate stubs for modules with missing type definitions.

At some point we will probably move to TypeScript.

.. _flow: https://flow.org/

Developing with SLDS
====================

MetaCI uses https://github.com/SalesforceFoundation/django-slds which imports version 2.1.2 of the Salesforce Lightning Design System.

You can find a CSS and component reference archived here: https://archive-2_1_2.lightningdesignsystem.com/
