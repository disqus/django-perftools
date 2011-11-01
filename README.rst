Logging Slow Requests
=====================

Perftools includes a logger that will monitor requests execution time. Once it hits
the defined threshold, it will log to the named ``perftools`` logger, including the
metadata for the request (as defined by Sentry's logging spec).

::

    from perftools.middleware.slowreq import SlowRequestLoggingMiddleware

    app = SlowRequestLoggingMiddleware(app, threshold=100) # in ms

Remote Profiling
================

Profiles a request and saves the results to disk.

::

    from perftools.middleware.remoteprof import RemoteProfilingMiddleware

    app = RemoteProfilingMiddleware(app, outpath='/var/data/cprofile-results/', percent=10) # 10% of requests

Query Counts
============

Logs requests which exceed a maximum number of queries.

::

    from perftools.middleware.querycount import QueryCountLoggingMiddleware

    app = QueryCountLoggingMiddleware(app, threshold=100) # number of queries
