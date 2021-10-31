import signal
import functools

from exceptions import TimeoutError


def timeout(seconds, error_message="Timeout"):
    """
    Function Timeout Decorator

    Ever had a function take forever in weird edge cases? In one case, a
    function was extracting URIs from a long string using regular expressions,
    and sometimes it was running into a bug in the Python regexp engine and
    would take minutes rather than milliseconds. The best solution was to
    install a timeout using an alarm signal and simply abort processing. This
    can conveniently be wrapped in a decorator.

    Example Usage:

        import time

        @timeout(1, 'Function slow; aborted')
        def slow_function():
            time.sleep(5)

    https://wiki.python.org/moin/PythonDecoratorLibrary#Function_Timeout
    """

    def decorated(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return functools.wraps(func)(wrapper)

    return decorated
