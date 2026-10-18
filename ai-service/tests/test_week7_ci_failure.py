
def test_week7_ci_detects_failure():
    """Intentional failure for Week 7 CI evidence."""
    assert 1 + 1 == 3, "Expected failure: CI is working correctly"
