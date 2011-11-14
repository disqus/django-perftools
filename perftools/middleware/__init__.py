"""
perftools.middleware
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

__all__ = ('SlowRequestLoggingMiddleware', 'RemoteProfilingMiddleware', 'QueryCountLoggingMiddleware')

import random
import threading

class Base(threading.local):
    def __init__(self, application, percent=100):
        self.percent = percent

    def should_run(self, environ):
        if self.percent == 100:
            return True
        return random.randint(0, 100) % self.percent == 0

from perftools.middleware.slowreq import SlowRequestLoggingMiddleware
from perftools.middleware.remoteprof import RemoteProfilingMiddleware
from perftools.middleware.querycount import QueryCountLoggingMiddleware

