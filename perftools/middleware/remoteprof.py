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
import simplejson
import sys
import time

from perftools.middleware import Base


class RemoteProfilingMiddleware(Base):
    logger = logging.getLogger(__name__)

    def __init__(self, application, outpath, threshold=0.5, **kwargs):
        self.application = application
        self.outpath = outpath
        self.threshold = threshold
        super(RemoteProfilingMiddleware, self).__init__(application, **kwargs)

    def __call__(self, environ, start_response):
        if not self.should_run(environ):
            return self.application(environ, start_response)

        profile = cProfile.Profile()

        start = time.time()
        try:
            return list(profile.runcall(self.application, environ, start_response))
        finally:
            stop = time.time()
            try:
                if (stop - start) > self.threshold:
                    self.report_result(profile, environ, start, stop, self.outpath)
            except Exception, e:
                self.logger.exception(e)

    def report_result(self, profile, environ, start, stop, outpath):
        ts_parts = map(lambda x: str(int(x)), divmod(start, 100000))
        randnum = random.randint(0, sys.maxint)
        outpath = os.path.join(self.outpath, ts_parts[0], ts_parts[1])
        outfile_base = '%s-%s' % (int(stop), randnum)

        if not os.path.exists(outpath):
            os.makedirs(outpath)

        profile.dump_stats(os.path.join(outpath, outfile_base + '.profile'))

        with open(os.path.join(outpath, outfile_base + '.json'), 'w') as fp:
            fp.write(simplejson.dumps({
                'environ': dict((k, v) for k, v in environ.iteritems() if isinstance(v, basestring)),
                'start_time': start,
                'stop_time': stop,
            }, indent=2))
