"""
perftools.middleware.slowreq
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

import inspect
import logging
import thread
import threading

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

from perftools.middleware import Base
from perftools.utils import get_culprit

try:
    # Available from Python >= 2.5
    from sys import _current_frames as threadframe
except ImportError:
    import threadframe as _threadframe
    # Wrapper to provide the same interface as the one from Python >= 2.5
    threadframe = lambda: _threadframe.dict()


class SlowRequestLoggingMiddleware(Base):
    def __init__(self, application, threshold=1, stacks=True, logger=None, **kwargs):
        self.application = application
        self.threshold = float(threshold) / 1000
        self.stacks = stacks
        self.logger = logger or logging.getLogger(__name__)
        super(SlowRequestLoggingMiddleware, self).__init__(application, **kwargs)

    def __call__(self, environ, start_response):
        if not self.should_run(environ):
            return self.application(environ, start_response)

        request = WSGIRequest(environ)

        timer = threading.Timer(self.threshold, self.log_request, args=[thread.get_ident(), request])
        timer.start()

        try:
            return list(self.application(environ, start_response))
        finally:
            timer.cancel()

    def get_parent_frame(self, parent_id):
        return threadframe()[parent_id]

    def get_frames(self, frame):
        return inspect.getouterframes(frame)

    def log_request(self, parent_id, request):
        try:
            parent_frame = self.get_parent_frame(parent_id)
        except KeyError:
            frames = []
            culprit = None
        else:
            frames = self.get_frames(parent_frame)
            culprit = get_culprit(frames, settings.INSTALLED_APPS)

        url = request.build_absolute_uri()

        self.logger.warning('Request exceeeded execution time threshold: %s', url, extra={
            'request': request,
            'view': culprit,
            'stack': frames,
            'url': url,
            'data': {
                'threshold': self.threshold,
            }
        })
