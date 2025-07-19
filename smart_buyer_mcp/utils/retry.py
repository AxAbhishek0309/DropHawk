import time
import functools

def retry(exceptions, tries=3, delay=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == tries - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator 