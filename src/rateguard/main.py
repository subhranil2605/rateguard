import time
import threading
from functools import wraps
from typing import Any, Callable, TypeVar


F = TypeVar("F", bound=Callable[..., Any])


def rate_limit(rpm: int) -> Callable[[F], F]:
    """
    Decorator to limit the number of function calls per minute.

    This decorator ensures that the decorated function is called at most 'rpm' times per minute.
    If a call is made before the allowed interval has passed since the last call, the decorator
    will sleep for the remaining time needed to enforce the rate limit.

    Args:
        rpm (int): Maximum number of function calls allowed per minute.

    Returns:
        Callable[[F], F]: The decorator function that can be applied to any callable.
    """
    # Calculate the interval in seconds between allowed calls.
    interval: float = 60.0 / rpm
    # Use a lock to synchronize access in multi-threaded scenarios.
    lock = threading.Lock()
    last_call_time: float = 0.0

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call_time
            with lock:
                now: float = time.time()
                elapsed: float = now - last_call_time

                # If the elapsed time since the last call is less than the interval,
                # sleep for the remaining time.
                if elapsed < interval:
                    time.sleep(interval - elapsed)

                # Update the time of the last function call.
                last_call_time = time.time()

            # Call the actual function and return its result.
            return func(*args, **kwargs)

        return wrapper

    return decorator
