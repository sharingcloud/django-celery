"""

Start the celery clock service from the Django management command.

"""
from __future__ import absolute_import, unicode_literals

from celery import VERSION as CELERY_VERSION
from celery.bin import beat

from djcelery.app import app
from djcelery.management.base import CeleryCommand

beat = beat.beat(app=app)


class Command(CeleryCommand):
    """Run the celery periodic task scheduler."""
    help = 'Old alias to the "celery beat" command.'
    if CELERY_VERSION[0] < 4:
        options = (
            tuple(CeleryCommand.options) +
            tuple(beat.get_options()) +
            tuple(getattr(beat, 'preload_options', ()))
        )
    else:
        def add_arguments(self, parser):
            super().add_arguments(parser)
            beat.add_arguments(parser)

            # Deprecated args
            parser.add_argument("--workdir", help="deprecated")

    def handle(self, *args, **options):
        beat.run(*args, **options)
