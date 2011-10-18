"""
perftools.middleware
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

from perftools.middleware.slowreq import SlowRequestLoggingMiddleware
from perftools.middleware.remoteprof import RemoteProfilingMiddleware

__all__ = ('SlowRequestLoggingMiddleware', 'RemoteProfilingMiddleware')

