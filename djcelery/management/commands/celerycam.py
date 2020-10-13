"""

Shortcut to the Django snapshot service.

"""
from __future__ import absolute_import, unicode_literals

from celery import VERSION as CELERY_VERSION
from celery.bin import events

from djcelery.app import app
from djcelery.management.base import CeleryCommand

ev = events.events(app=app)


class Command(CeleryCommand):
    """Run the celery curses event viewer."""
    help = 'Takes snapshots of the clusters state to the database.'
    if CELERY_VERSION[0] < 4:
        options = (
            tuple(CeleryCommand.options) +
            tuple(ev.get_options()) +
            tuple(getattr(ev, 'preload_options', ()))
        )
    else:
        def add_arguments(self, parser):
            super().add_arguments(parser)
            ev.add_arguments(parser)

            # Deprecated args
            parser.add_argument("--workdir", help="deprecated")

    def handle(self, *args, **options):
        """Handle the management command."""
        if not options["camera"]:
            options['camera'] = 'djcelery.snapshot.Camera'
        ev.run(*args, **options)
