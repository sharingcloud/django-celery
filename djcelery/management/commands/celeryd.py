"""

Start the celery daemon from the Django management command.

"""
from __future__ import absolute_import, unicode_literals

from celery import VERSION as CELERY_VERSION
from celery.bin import worker

from djcelery.app import app
from djcelery.management.base import CeleryCommand

worker = worker.worker(app=app)


class Command(CeleryCommand):
    """Run the celery daemon."""
    help = 'Old alias to the "celery worker" command.'
    if CELERY_VERSION[0] < 4:
        options = (
            tuple(CeleryCommand.options) +
            tuple(worker.get_options()) +
            tuple(getattr(worker, 'preload_options', ()))
        )
    else:
        def add_arguments(self, parser):
            super().add_arguments(parser)
            worker.add_arguments(parser)

    def handle(self, *args, **options):
        worker.check_args(args)
        worker.run(**options)
