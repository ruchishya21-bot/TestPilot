import os


class TargetConfig:

    APP_NAME = os.getenv(
        "TESTPILOT_APP_NAME",
        "TestPilot Demo Application"
    )

    BASE_URL = os.getenv(
        "TESTPILOT_BASE_URL",
        "http://127.0.0.1:5000"
    ).rstrip("/")

    HEALTH_ENDPOINT = os.getenv(
        "TESTPILOT_HEALTH_ENDPOINT",
        "/health"
    )

    REQUEST_TIMEOUT = int(
        os.getenv("TESTPILOT_REQUEST_TIMEOUT", "15")
    )

    HEADLESS = (
        os.getenv("TESTPILOT_HEADLESS", "false").lower()
        == "true"
    )

    @classmethod
    def get_url(cls, endpoint=""):
        if not endpoint:
            return cls.BASE_URL

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        return cls.BASE_URL + endpoint

    @classmethod
    def get_health_url(cls):
        return cls.get_url(cls.HEALTH_ENDPOINT)