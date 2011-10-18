import logging
import os.path
import pstats
import shutil
import sys
import time
import unittest2

from perftools.middleware.slowreq import SlowRequestLoggingMiddleware
from perftools.middleware.remoteprof import RemoteProfilingMiddleware

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASE_ENGINE='sqlite3',
        DATABASES={
            'default': {
                'ENGINE': 'sqlite3',
            },
        },
        INSTALLED_APPS=['tests'],
        ROOT_URLCONF='',
        DEBUG=False,
        TEMPLATE_DEBUG=True,
    )

class MockApp(object):
    def __init__(self, wait=0):
        self.wait = wait

    def __call__(self, environ, start_response):
        if self.wait:
            time.sleep(self.wait)
        return start_response()

class SlowRequestLoggingMiddlewareTest(unittest2.TestCase):
    def setUp(self):
        self.captured_logs = []

        class CaptureHandler(logging.Handler):
            def __init__(self, inst, level=logging.NOTSET):
                self.inst = inst
                super(CaptureHandler, self).__init__(level=level)

            def emit(self, record):
                self.inst.captured_logs.append(record)

        logger = logging.getLogger('perftools')
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.addHandler(CaptureHandler(self))

    def test_blocking(self):
        app = SlowRequestLoggingMiddleware(MockApp(wait=0.1), threshold=1)
        response = list(app({
            'REMOTE_ADDR': '127.0.0.1',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'test',
            'SERVER_PORT': '80',
            'wsgi.input': sys.stdin,
        }, lambda:''))
        self.assertEquals(response, list(''))
        self.assertEquals(len(self.captured_logs), 1)

        record = self.captured_logs[0]
        self.assertEquals(record.levelno, logging.WARNING)

        self.assertTrue(hasattr(record, 'request'))
        request = record.request
        self.assertTrue('SERVER_NAME' in request.META)
        self.assertEquals(request.META['SERVER_NAME'], 'test')

        self.assertTrue(hasattr(record, 'view'))
        self.assertEquals(record.view, 'tests.tests.test_blocking')

class AlwaysProfileMiddleware(RemoteProfilingMiddleware):
    def should_profile(self, environ):
        return True

class RemoteProfilingMiddlewareMiddlewareTest(unittest2.TestCase):
    def setUp(self):
        self.outpath = os.path.join(os.path.dirname(__file__), 'profiles')

    def tearDown(self):
        shutil.rmtree(self.outpath)

    def test_blocking(self):
        app = AlwaysProfileMiddleware(MockApp(wait=0.1), outpath=self.outpath)
        response = list(app({
            'REMOTE_ADDR': '127.0.0.1',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'test',
            'SERVER_PORT': '80',
            'wsgi.input': sys.stdin,
        }, lambda:''))

        self.assertEquals(response, list(''))
        dirs = os.listdir(self.outpath)
        self.assertEquals(len(dirs), 1)
        dirs_2 = os.listdir(os.path.join(self.outpath, dirs[0]))
        self.assertEquals(len(dirs_2), 1)
        dirs_3 = os.listdir(os.path.join(self.outpath, dirs[0], dirs_2[0]))
        self.assertEquals(len(dirs_3), 1)
        self.assertTrue(dirs_3[0].endswith('.profile'))

        stats = pstats.Stats(os.path.join(self.outpath, dirs[0], dirs_2[0], dirs_3[0]))
        self.assertNotEquals(stats.total_calls, 0)
        self.assertTrue(any(__file__ in c[0] for c in stats.stats.iterkeys()))
