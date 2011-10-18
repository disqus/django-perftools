"""
perftools.middleware.slowreq
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

import logging
import time
import thread
import threading

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

try:
    # Available from Python >= 2.5
    from sys import _current_frames as threadframe
except ImportError:
    import threadframe as _threadframe
    # Wrapper to provide the same interface as the one from Python >= 2.5
    threadframe = lambda: _threadframe.dict()

logger = logging.getLogger('perftools')

class RequestLogger(threading.Thread):
    def __init__(self, parent_id, request, threshold=100, logger=logger, stacks=False):
        super(RequestLogger, self).__init__()
        self.parent_id = parent_id
        self.request = request
        self.threshold = threshold
        self.logger = logger
        self.stacks = stacks
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def is_stopped(self):
        return self._stop.isSet()

    def get_parent_frame(self):
        return threadframe()[self.parent_id]

    def get_frames(self, frame):
        # TODO: look into using inspect.getouterframes()
        frames = []
        while frame:
            frames.append(frame)
            frame = frame.f_back

        frames = frames[::-1]

        return frames

    def get_culprit(self, frames):
        def contains(iterator, value):
            for k in iterator:
                if value.startswith(k):
                    return True
            return False

        modules = settings.INSTALLED_APPS

        best_guess = None
        for frame in frames:
            try:
                culprit = '.'.join([frame.f_globals['__name__'], frame.f_code.co_name])
            except:
                continue
            if contains(modules, culprit):
                if not best_guess:
                    best_guess = culprit
            elif best_guess:
                break

        return best_guess

    def log_request(self, elapsed):
        try:
            parent_frame = self.get_parent_frame()
        except KeyError:
            culprit = None
        else:
            frames = self.get_frames(parent_frame)
            culprit = self.get_culprit(frames)

        url = self.request.build_absolute_uri()

        self.logger.warning('Request exceeeded execution time threshold: %s', url, extra={
            'request': self.request,
            'view': culprit,
            'url': url,
            'stack': self.stacks,
            'data': {
                'threshold': self.threshold,
            }
        })

    def run(self):
        start = time.time()
        while not self.is_stopped():
            now = time.time()
            elapsed = (now - start) * 1000
            if elapsed > self.threshold:
                self.log_request(elapsed)
                self.stop()

            time.sleep(0.01)

class SlowRequestLoggingMiddleware(threading.local):
    def __init__(self, application, threshold=1, stacks=True):
        self.application = application
        self.threshold = threshold
        self.stacks = stacks

    def __call__(self, environ, start_response):
        request = WSGIRequest(environ)

        logger = RequestLogger(thread.get_ident(), request, self.threshold, stacks=self.stacks)
        logger.start()

        try:
            return self.application(environ, start_response)
        finally:
            logger.stop()
            logger.join(timeout=1)
