from __future__ import absolute_import, unicode_literals

from celery import VERSION as CELERY_VERSION
from celery.bin import celery

from djcelery.app import app
from djcelery.management.base import CeleryCommand

base = celery.CeleryCommand(app=app)


class Command(CeleryCommand):
    """The celery command."""
    help = 'celery commands, see celery help'
    if CELERY_VERSION[0] < 4:
        options = (
            tuple(CeleryCommand.options) +
            tuple(base.get_options() or ()) +
            tuple(getattr(base, 'preload_options', ()))
        )
    else:
        def add_arguments(self, parser):
            super().add_arguments(parser)
            base.add_arguments(parser)

    def run_from_argv(self, argv):
        argv = self.handle_default_options(argv)
        base.execute_from_commandline(
            ['{0[0]} {0[1]}'.format(argv)] + argv[2:],
        )
