"""
perftools.middleware.remoteprof
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

import cProfile
import logging
import os.path
import random
import sys
import time

from perftools.middleware import Base


class RemoteProfilingMiddleware(Base):
    logger = logging.getLogger(__name__)

    def __init__(self, application, outpath, **kwargs):
        self.application = application
        self.outpath = outpath
        super(RemoteProfilingMiddleware, self).__init__(application, **kwargs)

    def __call__(self, environ, start_response):
        if not self.should_run(environ):
            return self.application(environ, start_response)

        profile = cProfile.Profile()
        ts = map(str, divmod(time.time(), 1000))
        randnum = random.randint(0, sys.maxint)
        outpath = os.path.join(self.outpath, ts[0], ts[1])
        outfile = '%s-%s-%s.profile' % (ts[0], ts[1], randnum)

        try:
            return list(profile.runcall(self.application, environ, start_response))
        finally:
            try:
                if not os.path.exists(outpath):
                    os.makedirs(outpath)
                profile.dump_stats(os.path.join(outpath, outfile))
            except Exception, e:
                self.logger.exception(e)
