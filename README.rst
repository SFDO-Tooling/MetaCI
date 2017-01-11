mrbelvedereci
=============

A specialized lightweight CI server for building Salesforce projects from Github repositories using CumulusCI flows

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django


:License: BSD

What is This?
-------------

`mrbelvedereci` started as an extension of the CumulusCI 2 (https://github.com/SalesforceFoundation/CumulusCI/tree/feature/2.0) project.  After spending almost a year trying to find a cloud hosted CI service that could handle our needs for Salesforce managed package builds, the crazy idea was born: why not just write our own CI server specific to our needs?

A few key things to point out that made this compelling:

* Running our builds in any of the cloud CI platforms available felt like putting a square peg into a round hole.  Specifically, our builds aren't contained inside the build VM.  They build against an external resource, a Salesforce org.  That creates a lot of incorrect assumptions by the build system such as simple concurrency where anything can run concurrently since it's isolated in the build agent's VM.  That's not true for Salesforce projects and that false assumption creates many challenges with nasty workarounds at best. 
* CumulusCI 2 already contains all the logic to run all our build operations.  Unlike most CI scenarios, we have a very specific set of dependencies across all our builds.  Using a system that essentially gives us full flexibility by starting each build from a clean VM is way overkill for what we need.
* The available cloud CI options don't support burst pricing.  You pay to have X build containers reserved 24x7 for the month.  Our build patterns are far more burst oriented than that.  Maybe 80% of the time we're not building anything, 15% of the time we're building a few concurrent branches, and 5% of the time we're building lots at once and could need up to 25 concurrent builds.
* Heroku is a great platform for burst capacity architectures but no available CI systems run well on Heroku.

So, mrbelvedereci was started as a prototype of a crazy idea mid-November 2016, got prototype buy in mid-December 2016, and is going into production to replace Bamboo Cloud before January 31, 2017.

Features
--------

So, what does this thing actually do?

* Salesforce Lightning Design System UI
* Admins can configure Repositories, Plans, Orgs, and Services to configure build Plan
* A Plan can triggered by a regex match on a commit, a tag, or manually by an admin against any branch in the repo
* Builds are queued in a Redis message queue for background worker dynos to run the builds
* Integration with Hirefire.io provides automatic scaling up and down for worker dynos based on pending builds in the queue.  Hirefire checks every minute and makes the appropriate scaling action meaning scaling up to 25 concurrent builds takes at most one minute.
* Creating a commit or tag triggered Plan automatically creates the webhooks on the repo in Github
* Github webhooks trigger builds for any active matching Plans
* Simple concurrency logic: If the target org is persistent, attempt to get a lock to the org.  If a lock is obtained, run the build.  If not, reattempt the lock until abtained.  If the build runs against a scratch org, run concurrently.
* Each build Plan that has a value in its `context` field gets its own Github Commit Status set for Pending, InProgress, Success, and Fail/Error status.
* Support for private Repositories and Plans which hide builds from non-staff users
* Github OAuth login
* User configurable build notifications (coming soon)

Prerequisites
-------------

* A Github repository containing metadata for a managed package development project
* The cumulusci python package installed and configured on your local system so you can run deploy commands against your repo locally.  See http://cumulusci.readthedocs.io/en/latest/tutorial.html for more details on setting up CumulusCI locally.
* Optional, but highly recommended: Access to Salesforce DX.  If you configure the SFDX_CONFIG and SFDX_HUB_ORG config variables with the appropriate json you can use scratch orgs in your builds.  You'll need to configure your local environment to not use encryption when storing credentials in files so you can export the configs to mrbelvedereci.

Deploy to Heroku
----------------

Dive right in:

.. image:: https://www.herokucdn.com/deploy/button.svg
   :target: https://heroku.com/deploy

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

RQ Worker
^^^^^^^^^

This app comes with RQ, a Redis message queue library for Python.

Check the Procfile to see the commands used to run the workers on Heroku.  You can run a single local worker that watches all queues with:

.. code-block:: bash

    python manage.py rqworkers default short --worker-class mrbelvedereci.build.worker.RequeueingWorker


Email Server
^^^^^^^^^^^^

In development, it is often nice to be able to see emails that are being sent from your application. If you choose to use `MailHog`_ when generating the project a local SMTP server with a web interface will be available.

.. _mailhog: https://github.com/mailhog/MailHog

To start the service, make sure you have nodejs installed, and then type the following::

    $ npm install
    $ grunt serve

(After the first run you only need to type ``grunt serve``) This will start an email server that listens on ``127.0.0.1:1025`` in addition to starting your Django project and a watch task for live reload.

To view messages that are sent by your application, open your browser and go to ``http://127.0.0.1:8025``

The email server will exit when you exit the Grunt task on the CLI with Ctrl+C.

In Production, set up Sendgrid as a Heroku addon.

Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at  https://getsentry.com/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

Setting the Sentry DSN in production is optional but highly recommended.  Having good error management for your CI app is really nice!
