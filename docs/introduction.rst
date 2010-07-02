===============================================
 django-celery - Celery Integration for Django
===============================================

.. image:: http://cloud.github.com/downloads/ask/celery/celery_favicon_128.png

:Version: 2.0.0
:Web: http://celeryproject.org/
:Download: http://pypi.python.org/pypi/django-celery/
:Source: http://github.com/ask/django-celery/
:Keywords: celery, task queue, job queue, asynchronous, rabbitmq, amqp, redis,
  python, django, webhooks, queue, distributed

--

django-celery provides Celery integration for Django; Using the Django ORM
and cache backend for storing results, autodiscovery of task modules
for applications listed in ``INSTALLED_APPS``, and more.

`Celery`_ is a task queue/job queue based on distributed message passing.
It is focused on real-time operation, but supports scheduling as well.

The execution units, called tasks, are executed concurrently on a single or
more worker servers. Tasks can execute asynchronously (in the background) or synchronously
(wait until ready).

Celery is already used in production to process millions of tasks a day.

Celery is written in Python, but the protocol can be implemented in any
language. It can also `operate with other languages using webhooks`_.

The recommended message broker is `RabbitMQ`_, but support for `Redis`_ and
databases (`SQLAlchemy`_ / `Django`_) is also available.

.. _`Celery`: http://celeryproject.org/
.. _`RabbitMQ`: http://www.rabbitmq.com/
.. _`Redis`: http://code.google.com/p/redis/
.. _`Django`: http://www.djangoproject.org/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`operate with other languages using webhooks`:
    http://ask.github.com/celery/userguide/remote-tasks.html

.. contents::
    :local:

Using django-celery
===================

To enable ``django-celery`` for your project you need to add ``djcelery`` to
``INSTALLED_APPS``::

    INSTALLED_APPS += ("djcelery", )

Everything works the same as described in the `Celery User Manual`_, except you need
to invoke the programs through ``manage.py``:

=====================================  =====================================
**Program**                            **Replace with**
=====================================  =====================================
``celeryd``                            ``python manage.py celeryd``
``celerybeat``                         ``python manage.py celerybeat``
``camqadm``                            ``python manage.py camqadm``
``celeryev``                           ``python manage.py celeryev``
=====================================  =====================================

and instead of storing configuration values in ``celeryconfig.py``, you should use
your Django projects ``settings.py`` module.

If you're getting started for the first time you should read
`Getting started with django-celery`_

Documentation
=============

The `Celery User Manual`_ contains user guides, tutorials and an API
reference. Also the `django-celery documentation`_, contains information
about the Django integration.

.. _`django-celery documentation`:
    http://celeryproject.org/docs/django-celery/
.. _`Celery User Manual`: http://celeryproject.org/docs/
.. _`Getting started with django-celery`:
    http://celeryq.org/docs/django-celery/getting-started/first-steps-with-django.html

Installation
=============

You can install ``django-celery`` either via the Python Package Index (PyPI)
or from source.

To install using ``pip``,::

    $ pip install django-celery

To install using ``easy_install``,::

    $ easy_install django-celery

Downloading and installing from source
--------------------------------------

Download the latest version of ``django-celery`` from
http://pypi.python.org/pypi/django-celery/

You can install it by doing the following,::

    $ tar xvfz django-celery-0.0.0.tar.gz
    $ cd django-celery-0.0.0
    $ python setup.py build
    # python setup.py install # as root

Using the development version
------------------------------

You can clone the repository by doing the following::

    $ git clone git://github.com/ask/django-celery.git

Getting Help
============

Mailing list
------------

For discussions about the usage, development, and future of celery,
please join the `celery-users`_ mailing list. 

.. _`celery-users`: http://groups.google.com/group/celery-users/

IRC
---

Come chat with us on IRC. The `#celery`_ channel is located at the `Freenode`_
network.

.. _`#celery`: irc://irc.freenode.net/celery
.. _`Freenode`: http://freenode.net


Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them
to our issue tracker at http://github.com/ask/django-celery/issues/

Wiki
====

http://wiki.github.com/ask/celery/

Contributing
============

Development of ``django-celery`` happens at Github:
http://github.com/ask/django-celery

You are highly encouraged to participate in the development
of ``celery``. If you don't like Github (for some reason) you're welcome
to send regular patches.

License
=======

This software is licensed under the ``New BSD License``. See the ``LICENSE``
file in the top distribution directory for the full license text.

.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround