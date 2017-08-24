Heroku buildpack: Plone
=======================

This is a [Heroku buildpack](http://devcenter.heroku.com/articles/buildpacks) for Plone apps, powered by [zc.buildout](http://www.buildout.org/en/latest/). You can use the free-tier [Heroku](https://www.heroku.com/features) account to run a simple, production-quality, Plone site, absolutely for free, forever.

[![Build Status](https://travis-ci.org/plone/heroku-buildpack-plone.svg?branch=master)](https://travis-ci.org/plone/heroku-buildpack-plone)

Plone on Heroku
---------------

To run Plone on Heroku, you need to add the following ``heroku.cfg`` buildout configuration to your
repository (assuming you already have a ``buildout.cfg`` in your repository:

    [buildout]
    extends = buildout.cfg
    relative-paths = true

    [instance]
    relative-paths = true
    eggs +=
        RelStorage
        psycopg2
    rel-storage =
        keep-history false
        blob-dir /tmp/blobcache
        shared-blob-dir false
        type postgresql
        host PG_HOST
        dbname PG_DBNAME
        user PG_USER
        password PG_PASS

To understand the configuration changes, you need to know the following things about Heroku:

1. Heroku refers to a single server instance as a [dyno](https://devcenter.heroku.com/articles/dynos).

2. Heroku uses a two-step deployment workflow. In Plone's case, this buildpack first compiles a "runtime slug" with ``bin/buildout``. Then, Heroku copies the slug to a dyno and runs your app code against this slug with ``bin/instance console``. Because ``bin/buildout`` runs in a different place from ``bin/instance``, we need to fix some of the paths that buildout generates. The ``relative-paths`` flag fixes most of the paths for us, and then the buildpack uses ``sed`` to fix the rest of the paths in the buildout-generated ``zope.conf`` file.

3. At ``bin/buildout`` slug compile-time, the port number on which Plone will run is unknown. The port number is given as an environment variable only when Heroku runs the runtime slug on a dyno. Because Plone does not support environment variables in the ``zope.conf`` and does not read command-line parameters when ``bin/instance`` starts, this buildpack includes a ``configure_zopeconf.py`` script that injects port number from the environment variables into ``zope.conf``. This script runs just before starting the Plone instance on the dyno.

4. Heroku uses an ephemeral filesystem, which discards all data when you restart the dyno. However, Heroku provides world-class Postgres-as-a-service persistency options. To use this service, you need to configure Plone to use the ``RelStorage`` add-on, which enables support for relational DB. Similar to the port number, the ``configure_zopeconf.py`` script injects the DB connection settings from the environment variables into ``zope.conf``.

5. If you use a free-tier account, Heroku gives you one dyno instance per month. However, if your site has no traffic for longer than one hour, Heroku puts the dyno to sleep. If the dyno is asleep when the next request is made to your site, there will be some delay before a response is sent back (~20s for Heroku startup, ~20s for Plone startup). Subsequent requests will be served at a normal speed.

6. The free-tier PostgreSQL DB included in this buildpack has a limit of 10k rows. To stay below this limit, the ``heroku.cfg`` sets the ``keep-history false`` flag to discard transactional history. This flag disables the `Undo` Plone feature, but allows you to retain document history, keeps your DB small and manageable, and eliminates the need to regularly "pack" your DB. Based on preliminary tests, the 10k limit is reached after creating about 200 content items. After that, you need to move to the first paid PostgreSQL plan ($9/month) that increases the limit to 10 million rows. To check how many rows your DB uses, run ``heroku pg:info``.


Usage
-----

This section shows an example prompt session. This example assumes that you already [signed up for a Heroku account](https://id.heroku.com/signup) and successfully installed the [Heroku Toolbelt](https://toolbelt.heroku.com/):

    $ ls
    buildout.cfg heroku.cfg

    $ git add heroku.cfg
    $ git commit -m "add support for deploying on Heroku"

    $ heroku create --buildpack https://github.com/plone/heroku-buildpack-plone.git

    $ git push heroku master
    ...
    -----> Plone app detected
    -----> Use build cache
           Get buildout results from the previous build
    -----> Bootstrap buildout
           ...
    -----> Run bin/buildout
           ...
    -----> Fix paths in zope.conf
    -----> Copy results to cache
    -----> Copy results to slug
    -----> Copy configure_zopeconf.py script to slug
    -----> Discovering process types
           Procfile declares types    -> (none)
           Default types for Plone -> web

    $ heroku open
    $ heroku logs -t

The buildpack will detect that your app is a Plone app if your repo has the file `buildout.cfg` in the root. Heroku will use `zc.buildout` to install your dependencies and "vendor" a copy of the Plone runtime into your slug. The buildpack will define a default ``Procfile`` so you don't have to manually create it. The buildpack will also provision a free-tier PostgreSQL DB for persistence.

If you want general information about Heroku, you can read [how Heroku works](https://devcenter.heroku.com/articles/how-heroku-works).


Options
-------

### Running an arbitrary *.cfg file

To run an arbitrary *.cfg file such as ``production.cfg`` instead of the default ``heroku.cfg``, set the following environment variable:

    $ heroku config:add BUILDOUT_CFG=production.cfg

### Increase buildout verbosity

To increase the verbosity of ``bin/buildout``, set the following environment variable:

    $ heroku config:add BUILDOUT_VERBOSITY=-v

You can increase verbosity up to ``-vvvv``.

### Use arbitrary bootstrap.py

If you want to use an arbitrary ``bootstrap.py`` file, for example to enable support for ``zc.buildout`` 2.x, set the following environment variable:

    $ heroku config:add BOOTSTRAP_PY_URL=https://bootstrap.pypa.io/bootstrap-buildout.py

### Creating a demo for your Plone package

This buildpack allows you to easily create a demo of your Plone package for users to try the package out without the hassle of installing the package locally for themselves:

1. Add ``heroku.cfg`` to your package's repo, based on the sample ``heroku.cfg`` provided in this repo.
2. Add your package's specific configuration to the ``heroku.cfg`` file.
3. For a demo installation we want the DB to reset every once in a while, so visitors get a fresh install of Plone + your package, without content that other visitors created. This means, we want to go back to using ``Data.fs`` filestorage DB that will get removed every time the dyno running your demo is restarted. To go back to filestorage DB, just remove the ``rel-storage`` section from your ``heroku.cfg`` file.
4. Follow instructions in the `Usage` section of this README to deploy Plone, along with your package, to Heroku.
5. Optionally, extend the ``heroku.cfg`` with support for [creating a pre-populated Plone site instance with buildout](https://pypi.python.org/pypi/collective.recipe.plonesite).

If you get stuck, see how it's done in [collective.cover](https://github.com/collective/collective.cover/blob/master/heroku.cfg) and [plone.app.mosaic](https://github.com/plone/plone.app.mosaic/blob/master/heroku.cfg).

Migrating an existing Plone site to Heroku
------------------------------------------

When moving to Heroku, the main task is to migrate from a ZODB filesystem DB to a PostgreSQL relational DB. Migrations might differ, but generally you follow these steps:

1. Download ``Data.fs`` & BLOBs to your local machine.
2. Add the Heroku-specific configuration to the local ``heroku.cfg`` file.
3. Run ``git push heroku master`` to deploy your code to Heroku and create a PostgreSQL DB.
4. Run ``heroku config`` and write down the ``DATABASE_URL`` DB connection string.
5. Follow the instructions on https://pypi.python.org/pypi/RelStorage#id18 to complete the migration.

A sample ``zodbconvert.conf``:

    <filestorage source>
      path var/filestorage/Data.fs
      blob-dir var/blobstorage
    </filestorage>

    <relstorage destination>
      shared-blob-dir false
      blob-dir ./var/blobcache
      blob-cache-size 10mb
      keep-history false
        <postgresql>
          dsn dbname='<DATABASE>' user='<USER>' host='<HOST>' password='PASSWOR'
        </postgresql>
    </relstorage>


Additional resources
--------------------

* Blog post introducing Plone support on Heroku: http://www.niteoweb.com/blog/dear-plone-welcome-to-2014
* About Buildpacks: https://devcenter.heroku.com/articles/buildpacks
* About custom Buildpacks: https://devcenter.heroku.com/articles/buildpack-api


:sparkles: Bonus Karma Points :sparkles:
-----------------------------------------

The following tips n' tricks will help you make the most out of the Heroku environment.

### DNS & Cloudflare

By default, your app will be available on ``<APP_NAME>.herokuapp.com``. You can set a custom domain even with the free-tier account:

    $ heroku domains:add www.mydomain.com

Then you create a `CNAME` record that points to ``<APP_NAME>.herokuapp.com``. More info on https://devcenter.heroku.com/articles/custom-domains.

It's recommended to use [Cloudflare](http://cloudflare.com/) as a DNS provider. Their free-tier plan acts as a simple [CDN](https://en.wikipedia.org/wiki/Content_delivery_network), while their [AlwaysOnline](https://support.cloudflare.com/hc/en-us/articles/200168006-What-does-Always-Online-do-) feature helps when your free dyno [goes to sleep](https://devcenter.heroku.com/articles/dynos#dyno-sleeping).

### Virtual hosting

By default, your Plone site will be available at ``<DOMAIN>/Plone``. But normally, you want to have your Plone site served at root (``/``). No worries, Zope's Virtual Hosting Monster to the rescue!

Go to ``<DOMAIN>/Plone/virtual_hosting/manage_edit`` and add the following entry:

    <DOMAIN>/Plone

Click ``Save Changes`` and reload.

### Sending emails

The Heroku dyno does not include ``sendmail``. Even if it did, it is not recommended to send emails from an unknown server/IP if you want them to be delivered. Instead, provision the [Mailgun add-on](https://addons.heroku.com/mailgun) that gives you a free SMTP server for outgoing email, along with tracking delivery/open rates:

    $ heroku addons:add mailgun

Then navigate to the MailGun control panel to add and configure a domain for your app. Optionally, you can enable tracking of email delivery & clicks.

After your domain is ready, go to ``/@@mail-controlpanel`` on your Plone site and enter hostname/credentials from Mailgun.


### Log archival

Heroku stores [1500 most recent logs entries](https://devcenter.heroku.com/articles/logging#log-history-limits) that you can browse through with the ``heroko logs`` command. To keep a longer history of logs, provision the free-tier level of the [Papertrail add-on](https://addons.heroku.com/papertrail) to get 7 days of searchable log history plus the ability to store unlimited daily archives to your personal Amazon S3 account:

    $ heroku addons:add papertrail

### DB backups

To allow its users a good night's sleep, Heroku offers [daily DB backups](https://devcenter.heroku.com/articles/pgbackups). Let's enable them:

    $ heroku addons:add pgbackups:auto-month

As an exercise, the extra-paranoid among us can also configure [offsite DB backups to an Amazon S3 account](https://github.com/kbaum/pgbackups-archive-app).


### More Heroku add-ons

Browse through all [available add-ons](https://addons.heroku.com/) and see if any of them catches your attention.
