"""

Start detached worker node from the Django management utility.

"""
from __future__ import absolute_import, unicode_literals

import os
import sys

from celery import VERSION as CELERY_VERSION
from celery.bin import celeryd_detach

from djcelery.management.base import CeleryCommand


class Command(CeleryCommand):
    """Run the celery daemon."""
    help = 'Runs a detached Celery worker node.'
    if CELERY_VERSION[0] < 4:
        options = celeryd_detach.OPTION_LIST
    else:
        def add_arguments(self, parser):
            celeryd_detach.add_arguments(parser)

    def run_from_argv(self, argv):

        class detached(celeryd_detach.detached_celeryd):
            execv_argv = [os.path.abspath(sys.argv[0]), 'celery', 'worker']

        if CELERY_VERSION[0] >= 4:
            argv.remove("celeryd_detach")
        detached().execute_from_commandline(argv)
