import json
import pytest
import requests

from pathlib import Path
from config.target_config import TargetConfig


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "test_data"
    / "target_endpoints.json"
)


def load_test_data():

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.parametrize(
    "test_case",
    load_test_data(),
    ids=lambda case: case["name"]
)
def test_target_endpoint_status(test_case):

    url = TargetConfig.get_url(test_case["endpoint"])

    response = requests.get(
        url,
        timeout=TargetConfig.REQUEST_TIMEOUT
    )

    assert response.status_code == test_case["expected_status"], (
        f"{test_case['name']} failed. "
        f"Expected {test_case['expected_status']}, "
        f"received {response.status_code}."
    )