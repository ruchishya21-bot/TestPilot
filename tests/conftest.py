import os
import pytest
import time

from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from application.app import app
from application.database import db

from utilities import result_store
from utilities import flaky_tracker


_current_run_id = None
_run_start_time = None
_retry_counts = {}


def pytest_sessionstart(session):
    global _current_run_id
    global _run_start_time

    if hasattr(session.config, "workerinput"):
        return

    result_store.initialize_results_database()
    flaky_tracker.initialize_flaky_database()

    _run_start_time = time.perf_counter()
    _current_run_id = result_store.start_test_run()

    print(f"\nTestPilot Run Started: {_current_run_id}\n")


def pytest_sessionfinish(session, exitstatus):
    global _current_run_id
    global _run_start_time

    if hasattr(session.config, "workerinput"):
        return

    if _current_run_id is None:
        return

    duration = time.perf_counter() - _run_start_time

    result_store.finish_test_run(
        _current_run_id,
        duration
    )

    print("\nTestPilot execution history saved successfully.")


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):

    if _current_run_id is None:
        return

    # Detect a test attempt that will be retried.
    if report.outcome == "rerun":
        _retry_counts[report.nodeid] = (
            _retry_counts.get(report.nodeid, 0) + 1
        )
        return

    if report.when == "call":

        result_store.record_test_result(
            run_id=_current_run_id,
            node_id=report.nodeid,
            status=report.outcome,
            duration=report.duration,
            failure_details=(
                report.longreprtext if report.failed else None
            )
        )

        retry_count = _retry_counts.get(report.nodeid, 0)

        # A test that passed after one or more retries is flaky.
        if report.passed and retry_count > 0:

            flaky_tracker.record_flaky_test(
                run_id=_current_run_id,
                node_id=report.nodeid,
                retry_count=retry_count
            )

            print(
                f"\nFLAKY TEST DETECTED: {report.nodeid} "
                f"({retry_count} retries)"
            )

        _retry_counts.pop(report.nodeid, None)

    elif report.when == "setup" and (
        report.failed or report.skipped
    ):

        status = "error" if report.failed else "skipped"

        result_store.record_test_result(
            run_id=_current_run_id,
            node_id=report.nodeid,
            status=status,
            duration=report.duration,
            failure_details=(
                report.longreprtext if report.failed else None
            )
        )

    elif report.when == "teardown" and report.failed:

        result_store.record_test_result(
            run_id=_current_run_id,
            node_id=report.nodeid,
            status="error",
            duration=report.duration,
            failure_details=report.longreprtext
        )


@pytest.fixture
def client(tmp_path, monkeypatch):

    test_database = tmp_path / "testpilot_test.db"

    monkeypatch.setattr(
        db,
        "DATABASE_PATH",
        test_database
    )

    db.initialize_database()

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def driver():

    options = Options()

    options.binary_location = (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    )

    options.add_argument("--window-size=1440,1000")

    if os.getenv("CI", "").lower() == "true":
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    browser = webdriver.Chrome(options=options)

    yield browser

    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:

        browser = item.funcargs.get("driver")

        if browser:

            screenshot_directory = Path("screenshots")
            screenshot_directory.mkdir(
                parents=True,
                exist_ok=True
            )

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            filename = f"{item.name}_{timestamp}.png"

            screenshot_path = (
                screenshot_directory / filename
            )

            try:

                browser.save_screenshot(
                    str(screenshot_path)
                )

                print(
                    f"\nFailure screenshot saved: {screenshot_path}"
                )

            except Exception as error:

                print(
                    f"\nScreenshot capture failed: {error}"
                )

@pytest.fixture
def authenticated_client(client):

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["username"] = "testuser"

    return client
