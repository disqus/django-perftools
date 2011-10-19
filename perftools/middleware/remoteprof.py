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

class RemoteProfilingMiddleware(object):
    logger = logging.getLogger(__name__)

    def __init__(self, application, outpath, percent=100):
        self.application = application
        self.outpath = outpath
        self.percent = percent

    def __call__(self, environ, start_response):
        if not self.should_profile(environ):
            return self.application(environ, start_response)

        profile = cProfile.Profile()
        ts = map(str, divmod(time.time(), 1000))
        randnum = random.randint(0, sys.maxint)
        outpath = os.path.join(self.outpath, ts[0], ts[1])
        outfile = '%s-%s-%s.profile' % (ts[0], ts[1], randnum)

        try:
            return profile.runcall(self.application, environ, start_response)
        finally:
            try:
                if not os.path.exists(outpath):
                    os.makedirs(outpath)
                profile.dump_stats(os.path.join(outpath, outfile))
            except Exception, e:
                self.logger.exception(e)

    def should_profile(self, environ):
        return random.randint(0, sys.maxint) % self.percent == 0
        # from gargoyle import gargoyle
        # return gargoyle.is_active('remote_profiler')
