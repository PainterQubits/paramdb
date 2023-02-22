"""Helper functions for paramdb tests."""

import time
from datetime import datetime
from tests.conftest import CustomStruct, CustomParam


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


def update_param_and_assert_last_updated_changed(
    param: CustomParam, param_data: CustomStruct | CustomParam
) -> None:
    """
    Update the given parameter (assumed to be or exist within the given parameter data)
    and assert that the structure's last updated time correctly reflects that something
    was just updated.
    """
    start = datetime.now()
    sleep_for_datetime()
    param.number += 1
    sleep_for_datetime()
    end = datetime.now()
    assert param_data.last_updated is not None and start < param_data.last_updated < end
