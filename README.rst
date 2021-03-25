MetaCI
======

A specialized lightweight CI server for building Salesforce projects from Github repositories using CumulusCI flows

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django


:License: BSD

What is This?
-------------

`MetaCI` started as an extension of the CumulusCI 2 (https://github.com/SFDO-Tooling/CumulusCI/tree/feature/2.0) project.  After spending almost a year trying to find a cloud hosted CI service that could handle our needs for Salesforce managed package builds, the crazy idea was born: why not just write our own CI server specific to our needs?

A few key things to point out that made this compelling:

* Running our builds in any of the cloud CI platforms available felt like putting a square peg into a round hole.  Specifically, our builds aren't contained inside the build VM.  They build against an external resource, a Salesforce org.  That creates a lot of incorrect assumptions by the build system such as simple concurrency where anything can run concurrently since it's isolated in the build agent's VM.  That's not true for Salesforce projects and that false assumption creates many challenges with nasty workarounds at best. 
* CumulusCI 2 already contains all the logic to run all our build operations.  Unlike most CI scenarios, we have a very specific set of dependencies across all our builds.  Using a system that essentially gives us full flexibility by starting each build from a clean VM is way overkill for what we need.
* The available cloud CI options don't support burst pricing.  You pay to have X build containers reserved 24x7 for the month.  Our build patterns are far more burst oriented than that.  Maybe 80% of the time we're not building anything, 15% of the time we're building a few concurrent branches, and 5% of the time we're building lots at once and could need up to 25 concurrent builds.
* Heroku is a great platform for burst capacity architectures but no available CI systems run well on Heroku.

So, MetaCI was started as a prototype of a crazy idea mid-November 2016, got prototype buy in mid-December 2016, and is going into production to replace Bamboo Cloud before January 31, 2017.

Features
--------

So, what does this thing actually do?

* Salesforce Lightning Design System UI
* Admins can configure Repositories, Plans, Orgs, and Services to configure build Plan
* A Plan can be triggered by a regex match on a commit, a tag, or manually by an admin against any branch in the repo
* Builds are queued in a Redis message queue for background worker dynos to run the builds
* Automatic scaling up and down for worker dynos based on pending builds in the queue.
* Creating a commit or tag triggered Plan automatically creates the webhooks on the repo in Github
* Github webhooks trigger builds for any active matching Plans
* Simple concurrency logic: If the target org is persistent, attempt to get a lock to the org.  If a lock is obtained, run the build.  If not, reattempt the lock until obtained.  If the build runs against a scratch org, run concurrently.
* Each build Plan that has a value in its `context` field gets its own Github Commit Status set for Pending, InProgress, Success, and Fail/Error status.
* Support for private Repositories and Plans which hide builds from non-staff users
* Github OAuth login
* User configurable email notifications.  Notifications can be set up for success, fail, and error status on repositories, branches, and plans.

Prerequisites
-------------

* A Github repository containing metadata for a managed package development project
* The cumulusci python package installed and configured on your local system so you can run deploy commands against your repo locally.  See http://cumulusci.readthedocs.io/en/latest/tutorial.html for more details on setting up CumulusCI locally.
* Optional, but highly recommended: Access to Salesforce DX.  If you configure the SFDX_CONFIG and SFDX_HUB_ORG config variables with the appropriate json you can use scratch orgs in your builds.  You'll need to configure your local environment to not use encryption when storing credentials in files so you can export the configs to MetaCI.

You can also fork the CumulusCI-Test repository and use that as a demo since it is already configured for CumulusCI.  

Getting Started
---------------
MetaCI can be run locally or configured for use on Heroku.
For local setup see `running <https://github.com/SFDO-Tooling/MetaCI/blob/main/docs/running.rst>`_.

We're currently working on improving our documentation for deploying MetaCI on Heroku.
If you have questions about production setup, please reach out to the SFDO Release Engineering Team,
or post a question on the `CumulusCI Trailblazer Community Group <https://trailblazers.salesforce.com/_ui/core/chatter/groups/GroupProfilePage?g=0F9300000009M9Z>`_.
RQ Worker
^^^^^^^^^

This app comes with RQ, a Redis message queue library for Python.

Check the Procfile to see the commands used to run the workers on Heroku.  You can run a single local worker that watches all queues with:

.. code-block:: bash

    python manage.py metaci_rqworker high medium default short

Configuring Repositories
------------------------

The first step is to add your repositories.  Go to https://<your_app_name>.herokuapp.com/admin and log in using the admin user you created earlier.  Go to Repository and click Add.

Enter the repo name, owner name, and the url.  Currently only repositories on github.com are supported.  The github id will be automatically looked up for you so you can leave it blank.

Configuring Orgs
----------------

Any org you connect to your local CumulusCI keychain can be added to MetaCI as a build org.  Go to CUMULUSCI -> Orgs -> Add and give the org a name, select the repo, and paste in the results of `cumulusci2 org info <org_name>` on your local system.  Remember that org names are already namespaced by their repository so rather than package_name_feature, just call the org feature.


Configuring Services
--------------------

For a few flows, you need to have the github service configured in CumulusCI.  On your local system, run `cumulusci12 project show_github` to get the json to load add the `github` service under Service -> Add.  If you get an error, run `cumulusci2 project connect_github` to configure the github service in your local system then run show_github again.


Configuring Plans
-----------------

Plans are what ties together a repository, org, and CumulusCI flows.  Plans can have the following trigger types:

* **Commit**: Triggered by a commit pushed to the repository where the branch name matches a regex pattern
* **Tag**: Triggered by a tag pushed to the repository where the tag name matches a regex pattern
* **Manual**: Never automatically triggered, but like all Triggers, can be run by any staff member against any branch manually.

When you create Commit or Tag plans, the webhook should be automatically created in the repository to listen on the Github push event.  Creating the webhook requires that the GITHUB_USERNAME you used in the Heroku config for the app is an admin on the repository.

Additionally, you can define a Plan Repository Trigger that will trigger a plan based on another plan. For example, you could create a trigger such that when Plan X for Repository A completes successfully, Plan Y for Repository B is queued. This is especially helpful when building against upstream dependencies.

Private Plans & Repositories
----------------------------

You can set Plans and Repositories and Private.  When a Plan or Repository is private, the Plan or Repository and its builds will not show up in the public view.  They will show up for any user with the `is_staff` permission.

To set up user logins using Github, go to /admin and create a new Social App.  Create a new OAuth Application in your Github Settings on github.com to get the client id and secret info.  Once created, have your users go to https://<your_app_name>.herokuapp.com/accounts/github/login to login via Github.  Once they log in you can go to Users under admin and check the is_staff field for your staff users.

Notifications
-------------

Click the bell icon at the top to view the My Notifications page (/notifications) where you can view and add your notifications.

Automatic Scaling
-----------------

MetaCI can be configured to monitor its own build queue and scale its own Heroku dynos based on load in multiple Heroku Apps. It will check the queue once a minute and add worker dynos when needed. Once all builds are complete, all worker dynos will be shut down. Heroku only bills for the dyno seconds used, so this scaling can save money while allowing for greater concurrency when desired.

To configure autoscaling:

1. Set the METACI_MAX_WORKERS setting to the maximum number of dynos you'd like to scale up to.
2. Set the METACI_WORKER_RESERVE setting to the number of dynos you'd like to reserve for high-priority builds. (Optional; defaults to 1.)
3. Set up a Heroku user with access to this app, and create an authorization token using ``heroku authorizations:create``. Set the HEROKU_TOKEN setting to this authorization token.
4. Set the AUTOSCALERS setting as a dict in the following format: {'app_name : {'app_name': name, 'worker_type': type, 'max_workers': METACI_MAX_WORKERS, 'worker_reserve': METACI_WORKER_RESERVE, 'queues': [list of queues]}}. You may list more than one Heroku app in the in AUTOSCALERS setting and MetaCI will scale them all up and down at the same time.
    1. app_name - The name of the Heroku App.
    2. queues - a list of redis queues to monitor
    3. worker_type - The name of the worker dynos allocated for the given queues.
    4. max_workers - See METACI_MAX_WORKERS
    5. worker_reserve - See METACI_WORKER_RESERVE


One-Off Builds
~~~~~~~~~~~~~~

In some environments, such as Heroku, it is helpful to run builds in
environments which are spun up for just a single build. In Heroku, builds
created in this way will not share their finite lifespan (24 hours) with
previous builds. They also are not restarted when the app is updated.

You can specify the Python class to use for one-off builds with the
METACI_LONG_RUNNING_BUILD_CLASS environment variable, but the defaults
work well in Heroku.

You can specify the configuration for the class in JSON with an 
environment variable called METACI_LONG_RUNNING_BUILD_CONFIG.

For Heroku, this is a dictionary with a single key, like this:

    METACI_LONG_RUNNING_BUILD_CONFIG = {"app_name": "my-app"}

my-app would be replaced with the name of the Heroku App that should
be used.

Note: We anticipate that you might run into autoscaling logic
errors if you try to use one of your AUTOSCALERS apps for one-off
dynos as well because they both eat into the same quota but the
autoscaler class only knows about the persistent dynos. Perhaps
if your usage never approaches its quota then this will not
cause problems for you. This is not a tested or supported configuration.

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

In Production, set up Mailgun as a Heroku addon.

Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at  https://getsentry.com/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

Setting the Sentry DSN in production is optional but highly recommended.  Having good error management for your CI app is really nice!
