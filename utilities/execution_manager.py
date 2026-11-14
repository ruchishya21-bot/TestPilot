
import json
import os
import subprocess
import sys
import threading
import uuid

from pathlib import Path
from datetime import datetime

from utilities.target_validator import validate_target


BASE_DIR = Path(__file__).resolve().parents[1]

REPORTS_DIR = BASE_DIR / "reports"
LOG_FILE = REPORTS_DIR / "execution.log"
STATE_FILE = REPORTS_DIR / "execution_state.json"

ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
HTML_REPORT = REPORTS_DIR / "report.html"

_lock = threading.Lock()
_process = None


TEST_SUITES = {
    "all": {
        "label": "All Tests",
        "arguments": ["tests"]
    },

    "parallel": {
        "label": "Parallel All Tests (2 Workers)",
        "arguments": ["tests", "-n", "2"]
    },

    "api": {
        "label": "API Tests",
        "arguments": ["tests/api", "-m", "api"]
    },

    "ui": {
        "label": "UI Tests",
        "arguments": ["tests/ui", "-m", "ui"]
    },

    "database": {
        "label": "Database Tests",
        "arguments": ["tests/database", "-m", "database"]
    },

    "regression": {
        "label": "Regression Tests",
        "arguments": ["tests", "-m", "regression"]
    }
}


def ensure_directories():

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_state():

    ensure_directories()

    if not STATE_FILE.exists():

        return {
            "status": "idle",
            "test_type": None,
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "pid": None
        }

    try:

        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return {
            "status": "idle",
            "test_type": None,
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "pid": None
        }


def write_state(state):

    ensure_directories()

    temporary_file = STATE_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)

    temporary_file.replace(STATE_FILE)


def is_process_running(pid):

    if not pid:
        return False

    try:
        os.kill(int(pid), 0)
        return True

    except (OSError, ValueError, TypeError):
        return False


def get_execution_status():

    global _process

    with _lock:

        state = read_state()

        if state.get("status") != "running":
            return state

        if _process is not None and _process.poll() is not None:

            state["status"] = (
                "completed"
                if _process.returncode == 0
                else "failed"
            )

            state["exit_code"] = _process.returncode

            state["finished_at"] = datetime.now().isoformat(
                timespec="seconds"
            )

            write_state(state)

            _process = None

            return state

        if not is_process_running(state.get("pid")):

            state["status"] = "interrupted"

            state["finished_at"] = datetime.now().isoformat(
                timespec="seconds"
            )

            write_state(state)

        return state


def start_execution(test_type="all"):

    global _process

    if test_type not in TEST_SUITES:
        raise ValueError("Invalid test suite selected.")

    # STEP 1: Validate the configured target application.

    target_result = validate_target()

    if not target_result["healthy"]:

        raise RuntimeError(
            "Target application validation failed: "
            + target_result["message"]
        )

    # STEP 2: Check execution state and start Pytest.

    with _lock:

        current_state = read_state()

        if current_state.get("status") == "running":

            if is_process_running(current_state.get("pid")):

                raise RuntimeError(
                    "A test execution is already running."
                )

            current_state["status"] = "interrupted"

            current_state["finished_at"] = datetime.now().isoformat(
                timespec="seconds"
            )

            write_state(current_state)

        ensure_directories()

        suite = TEST_SUITES[test_type]

        # Create a separate Allure results directory for every run.

        run_folder = (
            "run_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:8]
        )

        run_allure_dir = ALLURE_RESULTS_DIR / run_folder

        run_allure_dir.mkdir(parents=True, exist_ok=False)

        # Build Pytest command.

        command = [
            sys.executable,
            "-m",
            "pytest",
            *suite["arguments"],
            "--html=" + str(HTML_REPORT),
            "--self-contained-html",
            "--alluredir=" + str(run_allure_dir)
        ]

        try:

            with open(LOG_FILE, "w", encoding="utf-8") as log:

                _process = subprocess.Popen(
                    command,
                    cwd=BASE_DIR,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=(
                        subprocess.CREATE_NEW_PROCESS_GROUP
                        if os.name == "nt"
                        else 0
                    )
                )

        except OSError:

            _process = None
            raise

        # STEP 3: Save execution state.

        state = {
            "status": "running",

            "test_type": test_type,

            "test_label": suite["label"],

            "started_at": datetime.now().isoformat(
                timespec="seconds"
            ),

            "finished_at": None,

            "exit_code": None,

            "pid": _process.pid,

            "command": command,

            "allure_results": str(
                run_allure_dir.relative_to(BASE_DIR)
            ),

            "target_validation": {
                "application": target_result["application"],
                "base_url": target_result["base_url"],
                "healthy": target_result["healthy"],
                "status_code": target_result["status_code"]
            }
        }

        write_state(state)

        return state


def get_execution_log():

    ensure_directories()

    if not LOG_FILE.exists():
        return "No execution logs available yet."

    try:

        with open(LOG_FILE, "r", encoding="utf-8") as file:
            return file.read()

    except OSError:

        return "Unable to read execution log."
