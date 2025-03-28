import time
from rateguard.main import rate_limit


def test_rate_limit_spacing():
    """
    Test that multiple calls to a rate-limited function are spaced by at least the minimum interval.
    """
    call_times = []

    @rate_limit(60)  # 60 calls per minute => 1 call per second.
    def test_func() -> None:
        call_times.append(time.time())

    # Call the test function three times.
    test_func()
    test_func()
    test_func()

    # There should be 3 timestamps recorded.
    assert len(call_times) == 3

    # Check that each call (except the first) is at least 1 second apart.
    for i in range(1, len(call_times)):
        elapsed = call_times[i] - call_times[i - 1]
        assert elapsed >= 1.0, f"Elapsed time {elapsed} is less than 1 second."


def test_return_value_unchanged():
    """
    Test that the decorator does not alter the function's return value.
    """

    @rate_limit(10)
    def add(a: int, b: int) -> int:
        return a + b

    result = add(3, 4)
    assert result == 7, f"Expected 7, got {result}"
