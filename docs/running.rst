===============================
Local Machine Development Setup
===============================

Clone The Project
=================

::

    git clone git@github.com:SFDO-Tooling/MetaCI
    cd MetaCI


Configuring MetaCI
==================

There are a number of environment variables which need to be configured in order to run MetaCI.
The easiest way to set these up is to copy our example ``env.example`` file::

    cp env.example env

Then edit ``env`` to fill in the necessary settings.
Please see `<./docs/configuring.rst>`_ for more details.

To activate the configuration, run::

    source env

You must do this each time you open a new terminal before working on MetaCI.


Install MetaCI
==============

MetaCI development requires Python v3.8. If ``which python3.8`` returns a
non-empty path, it's already installed and you can continue to the next step. If
it returns nothing, then install Python v3.8 using ``brew install python``, or
from `Python.org`_.

.. _Python.org: https://www.python.org/downloads/

Python software should always be installed into a "virtualenv" (virtual environment)
to make sure that its dependencies are isolated from other Python software on your machine.
To create a new virtualenv, run::

    python3.8 -m venv venv
    rehash

Now you can install MetaCI's Python dependencies::

    make dev-install


Installing Javascript Requirements
==================================

The project-local version of `Node.js`_ is bundled with the repo and can be
unpacked locally (in the git-ignored ``node/`` directory), so you don't have to
install it system-wide (and possibly conflict with other projects wanting other
Node versions).

To install the project-local version of Node (and `yarn`_)::

    bin/unpack-node
    rehash

If you can run ``which node`` and see a path inside your project directory ending with
``.../node/bin/node``, then you've got it set up right and can move on.

Then use ``yarn`` to install dependencies::

    yarn

.. _Node.js: http://nodejs.org
.. _yarn: https://yarnpkg.com/


Set Up The Database
===================

Assuming you have `Postgres <https://www.postgresql.org/download/>`_ installed
and running locally::

    createdb metaci

Then run the initial migrations::

    ./manage.py migrate

Run this command if you would like to populate the database with fake testing
data:

    ./manage.py populate_db

Set up Redis
============

The local development server requires `Redis <https://redis.io/>`_ to manage
background worker tasks. If you can successfully run ``redis-cli ping`` and see
output ``PONG``, then you have Redis installed and running. Otherwise, run
``brew install redis`` (followed by ``brew services start redis``) or refer to
the `Redis Quick Start`_.

.. _Redis Quick Start: https://redis.io/topics/quickstart


Create A Superuser
==================

To use the Django admin UI, you'll need to create a superuser::

    ./manage.py createsuperuser


Run The Server
==============

To run the local development server::

    yarn serve

This starts a process running Django, a process running Node, and an ``rq`` worker process.
The running server will be available at `<http://localhost:8080/>`_.

Admin Login
===========

To log in as your superuser, use the admin URL (NOT the Log In link at upper right, which is for logging in via GitHub):

    http://localhost:8000/admin
