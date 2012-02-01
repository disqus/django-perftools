def contains(iterator, value):
    for k in iterator:
        if value.startswith(k):
            return True
    return False


def get_culprit(frames, modules=[]):
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
