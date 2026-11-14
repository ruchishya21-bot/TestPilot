import pytest

from utilities.target_validator import validate_target


@pytest.mark.smoke
def test_target_application_is_reachable():

    result = validate_target()

    assert result["reachable"] is True, (
        f"Target application is unreachable: {result['message']}"
    )


@pytest.mark.smoke
def test_target_application_is_healthy():

    result = validate_target()

    assert result["healthy"] is True, (
        f"Target application is unhealthy: {result['message']}"
    )

    assert result["status_code"] == 200