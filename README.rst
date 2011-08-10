Logging Slow Requests
=====================

Perftools includes a logger that will monitor requests execution time. Once it hits
the defined threshold, it will log to the named ``perftools`` logger, including the
metadata for the request (as defined by Sentry's logging spec).

::

    import perftools.middleware.SlowRequestLoggingMiddleware
    
    app = SlowRequestLoggingMiddleware(app, threshold=100) # in ms