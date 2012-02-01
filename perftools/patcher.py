def _dot_lookup(thing, comp, import_path):
    try:
        return getattr(thing, comp)
    except AttributeError:
        __import__(import_path)
        return getattr(thing, comp)


def import_string(target):
    components = target.split('.')
    import_path = components.pop(0)
    thing = __import__(import_path)

    for comp in components:
        import_path += ".%s" % comp
        thing = _dot_lookup(thing, comp, import_path)
    return thing


class Patcher(object):
    def __init__(self, target, callback):
        target, attribute = target.rsplit('.', 1)
        self.target = import_string(target)
        self.attribute = attribute
        self.callback = callback

    def __enter__(self, *args, **kwargs):
        self.original = getattr(self.target, self.attribute)

        def wrapped(*args, **kwargs):
            return self.callback(self.original, *args, **kwargs)
        wrapped.__name__ = self.attribute

        setattr(self.target, self.attribute, wrapped)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        setattr(self.target, self.attribute, self.original)


def patch(target):
    """
    from disqus.utils import monkey

    @monkey.patch('psycopg2.connect')
    def psycopg2_connect(func, *args, **kwargs):
        print "Zomg im connecting!!!!"
        return func(*args, **kwargs)
    """
    target, attribute = target.rsplit('.', 1)
    target = import_string(target)
    func = getattr(target, attribute)

    def inner(callback):
        if getattr(func, '__patcher__', False):
            return func

        def wrapped(*args, **kwargs):
            return callback(func, *args, **kwargs)

        actual = getattr(func, '__wrapped__', func)
        wrapped.__wrapped__ = actual
        wrapped.__doc__ = getattr(actual, '__doc__', None)
        wrapped.__name__ = actual.__name__
        wrapped.__patcher__ = True

        setattr(target, attribute, wrapped)
        return wrapped
    return inner
