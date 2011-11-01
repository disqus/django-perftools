"""
perftools.middleware.slowreq
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

import logging
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

class SlowRequestLoggingMiddleware(threading.local):
    def __init__(self, application, threshold=1, stacks=True, logger=logger):
        self.application = application
        self.threshold = float(threshold) / 1000
        self.stacks = stacks
        self.logger = logger

    def __call__(self, environ, start_response):
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

    def log_request(self, parent_id, request):
        try:
            parent_frame = self.get_parent_frame(parent_id)
        except KeyError:
            frames = []
            culprit = None
        else:
            frames = self.get_frames(parent_frame)
            culprit = self.get_culprit(frames)

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