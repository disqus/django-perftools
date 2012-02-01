"""
perftools.middleware.querycount
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

import logging
import threading

from django.core.handlers.wsgi import WSGIRequest
from perftools.middleware import Base
from perftools.patcher import Patcher


class State(threading.local):
    def __init__(self):
        self.count = 0
        self.queries = []


class CursorWrapper(object):
    def __init__(self, cursor, connection, state, queries=False):
        self.cursor = cursor
        self.connection = connection
        self._state = state
        self._queries = queries

    def _incr(self, sql, params):
        if self._queries:
            self._state.queries.append((sql, params))
        self._state.count += 1

    def execute(self, sql, params=()):
        try:
            return self.cursor.execute(sql, params)
        finally:
            self._incr(sql, params)

    def executemany(self, sql, paramlist):
        try:
            return self.cursor.executemany(sql, paramlist)
        finally:
            self._incr(sql, paramlist)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)


def get_cursor_wrapper(state, queries=False):
    def cursor(func, self, *args, **kwargs):
        result = func(self, *args, **kwargs)

        return CursorWrapper(result, self, state, queries=queries)
    return cursor


class QueryCountLoggingMiddleware(Base):
    def __init__(self, application, threshold=1, stacks=False, queries=False, logger=None, **kwargs):
        self.application = application
        self.threshold = threshold
        self.stacks = stacks
        self.logger = logger or logging.getLogger(__name__)
        self.queries = queries
        super(QueryCountLoggingMiddleware, self).__init__(application, **kwargs)

    def __call__(self, environ, start_response):
        if not self.should_run(environ):
            return self.application(environ, start_response)

        state = State()
        cursor = get_cursor_wrapper(state, queries=self.queries)

        with Patcher('django.db.backends.BaseDatabaseWrapper.cursor', cursor):
            try:
                return list(self.application(environ, start_response))
            finally:
                if state.count > self.threshold:
                    self.log_request(WSGIRequest(environ), state)

    def log_request(self, request, state):
        url = request.build_absolute_uri()

        self.logger.warning('Request exceeeded query count threshold: %s', url, extra={
            'request': request,
            'stack': self.stacks,
            'url': url,
            'data': {
                'threshold': self.threshold,
                'query_count': state.count,
                'queries': [(k, repr(v)) for k, v in state.queries],
            }
        })
