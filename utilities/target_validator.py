import requests

from config.target_config import TargetConfig


def validate_target():

    health_url = TargetConfig.get_health_url()

    result = {
        "application": TargetConfig.APP_NAME,
        "base_url": TargetConfig.BASE_URL,
        "health_url": health_url,
        "reachable": False,
        "healthy": False,
        "status_code": None,
        "message": None
    }

    try:
        response = requests.get(
            health_url,
            timeout=TargetConfig.REQUEST_TIMEOUT
        )

        result["reachable"] = True
        result["status_code"] = response.status_code

        if response.ok:
            result["healthy"] = True
            result["message"] = "Target application is healthy."
        else:
            result["message"] = (
                f"Health check failed with HTTP {response.status_code}."
            )

    except requests.exceptions.ConnectionError:
        result["message"] = "Cannot connect to target application."

    except requests.exceptions.Timeout:
        result["message"] = "Target application request timed out."

    except requests.exceptions.RequestException as error:
        result["message"] = str(error)

    return result


if __name__ == "__main__":

    validation = validate_target()

    print("\n========== TESTPILOT TARGET VALIDATION ==========")

    for key, value in validation.items():
        print(f"{key}: {value}")

    print("=================================================")