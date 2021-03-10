===============================
Local Machine Development Setup
===============================

Cloning The Project
===================

::

    git clone git@github.com:SFDO-Tooling/MetaCI
    cd MetaCI

Making A Virtual Env
====================

MetaCI development requires Python v3.8. If ``which python3.8`` returns a
non-empty path, it's already installed and you can continue to the next step. If
it returns nothing, then install Python v3.8 using ``brew install python``, or
from `Python.org`_.

.. _Python.org: https://www.python.org/downloads/

There are a variety of tools that let you set up environment variables
temporarily for a particular "environment" or directory. We use
`virtualenvwrapper`_. Assuming you're in the repo root, do the following to
create a virtualenv (once you have `virtualenvwrapper`_ installed locally)::

    mkvirtualenv metaci --python=$(which python3.8)
    setvirtualenvproject

Install Python requirements::

    pip install -r requirements/local.txt

Copy the ``.env`` file to config/settings/.env::

    cp env.example config/settings/.env

Edit this file to fill in values for the missing settings, especially
for connecting to GitHub. Please see `<./docs/configuring.rst>`_
for more details.
 
Now run ``workon metaci`` to set those environment variables.

Your ``PATH`` (and environment variables) will be updated when you
``workon metaci`` and restored when you ``deactivate``. This will make sure
that whenever you are working on the project, you use the project-specific version of Node
instead of any system-wide Node you may have.

**All of the remaining steps assume that you have the virtualenv activated
("workon metaci").**

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/

.. _Personal Access Token: https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

Installing JavaScript Requirements
==================================

The project-local version of `Node.js`_ is bundled with the repo and can be
unpacked locally (in the git-ignored ``node/`` directory), so you don't have to
install it system-wide (and possibly conflict with other projects wanting other
Node versions).

To install the project-local version of Node (and `yarn`_)::

    bin/unpack-node

Make sure the local node bin directory is added to your PATH (you'll need to
do this every time you open a new terminal before you run yarn commands for this project,
so you might want to add it to your shell's init script)::

    PATH=./node/bin:$PATH

If you can run ``which node`` and see a path inside your project directory ending with
``.../node/bin/node``, then you've got it set up right and can move on.

Then use ``yarn`` to install dependencies::

    yarn

.. _Node.js: http://nodejs.org
.. _yarn: https://yarnpkg.com/

Setting Up The Database
=======================

Assuming you have `Postgres <https://www.postgresql.org/download/>`_ installed
and running locally::

    createdb metaci

Then run the initial migrations::

    ./manage.py migrate

Run this command if you would like to populate the database with fake testing
data:

    ./manage.py populate_db


Creating A Superuser
====================

To use the Django admin UI, you'll need to create a superuser::

    ./manage.py createsuperuser

You'll want to login to your user through the Admin URL rather
than through the visible login button.

    http://localhost:8000/admin/login

Running The Server
==================

The local development server requires `Redis <https://redis.io/>`_ to manage
background worker tasks. If you can successfully run ``redis-cli ping`` and see
output ``PONG``, then you have Redis installed and running. Otherwise, run
``brew install redis`` (followed by ``brew services start redis``) or refer to
the `Redis Quick Start`_.

To run the local development server::

    yarn serve

This starts a process running Django, a process running Node, and an ``rq`` worker process.
The running server will be available at `<http://localhost:8080/>`_.

.. _Redis Quick Start: https://redis.io/topics/quickstart
