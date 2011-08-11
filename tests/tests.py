import logging
import sys
import time
import unittest2

from perftools.middleware import SlowRequestLoggingMiddleware

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
        response = app({
            'REMOTE_ADDR': '127.0.0.1',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'test',
            'SERVER_PORT': '80',
            'wsgi.input': sys.stdin,
        }, lambda:'')
        self.assertEquals(len(self.captured_logs), 1)
        
        record = self.captured_logs[0]
        self.assertEquals(record.levelno, logging.WARNING)

        self.assertTrue(hasattr(record, 'request'))
        request = record.request
        self.assertTrue('SERVER_NAME' in request.META)
        self.assertEquals(request.META['SERVER_NAME'], 'test')
