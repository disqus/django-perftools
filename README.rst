Usage
=====

::

    import perftools.middleware.SlowRequestLoggingMiddleware
    app = SlowRequestLoggingMiddleware(app, threshold=100) # in ms