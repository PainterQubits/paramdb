"""Helper functions for paramdb tests."""

import time


def sleep_for_datetime() -> None:
    """
    Wait for a short amount of time so that following calls to `datetime.now()` are
    different than those that come before.

    This is necessary because a `datetime` object is only precise to microseconds (see
    https://docs.python.org/3/library/datetime.html#datetime-objects), whereas modern
    computers execute instructions faster than this. So without waiting, it is difficult
    to ensure that something is using `datetime.now()`.
    """
    time.sleep(0.001)  # Wait for one millisecond
