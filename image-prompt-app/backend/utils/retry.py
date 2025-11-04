import time
import random
from functools import wraps

def retry_with_exponential_backoff(
    tries=3,
    base_delay=0.6,
    max_delay=10.0,
    jitter=True,
    retry_on_exceptions=(Exception,),
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for i in range(tries):
                try:
                    return func(*args, **kwargs)
                except retry_on_exceptions as e:
                    if i == tries - 1:
                        raise
                    delay = min(delay * 2, max_delay)
                    if jitter:
                        delay += random.uniform(0, delay / 2)
                    time.sleep(delay)
        return wrapper
    return decorator
