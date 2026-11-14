import sqlite3
import uuid

from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DB_PATH = BASE_DIR / "reports" / "testpilot_results.db"


def get_results_connection():
    RESULTS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(RESULTS_DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_results_database():

    connection = get_results_connection()

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            duration REAL DEFAULT 0,
            total INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            skipped INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running'
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            node_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            duration REAL DEFAULT 0,
            failure_details TEXT,
            screenshot_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES test_runs(id),
            UNIQUE(run_id, node_id)
        );
    """)

    connection.commit()
    connection.close()


def start_test_run():

    run_id = str(uuid.uuid4())

    connection = get_results_connection()

    connection.execute(
        """
        INSERT INTO test_runs (id, started_at, status)
        VALUES (?, ?, ?)
        """,
        (
            run_id,
            datetime.now().isoformat(timespec="seconds"),
            "running"
        )
    )

    connection.commit()
    connection.close()

    return run_id


def get_test_category(node_id):

    if "tests/api/" in node_id:
        return "API"

    if "tests/database/" in node_id:
        return "Database"

    if "tests/functional/" in node_id:
        return "Functional"

    if "tests/ui/" in node_id:
        return "UI"

    return "Other"


def find_latest_screenshot(test_name):

    screenshot_directory = BASE_DIR / "screenshots"

    if not screenshot_directory.exists():
        return None

    screenshots = list(
        screenshot_directory.glob(f"{test_name}_*.png")
    )

    if not screenshots:
        return None

    latest_screenshot = max(
        screenshots,
        key=lambda file: file.stat().st_mtime
    )

    return str(latest_screenshot.relative_to(BASE_DIR))


def record_test_result(
    run_id,
    node_id,
    status,
    duration,
    failure_details=None
):

    test_name = node_id.split("::")[-1]
    category = get_test_category(node_id)

    screenshot_path = None

    if status in ("failed", "error"):
        screenshot_path = find_latest_screenshot(test_name)

    connection = get_results_connection()

    connection.execute(
        """
        INSERT INTO test_results (
            run_id,
            node_id,
            test_name,
            category,
            status,
            duration,
            failure_details,
            screenshot_path,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(run_id, node_id)
        DO UPDATE SET
            status = excluded.status,
            duration = excluded.duration,
            failure_details = excluded.failure_details,
            screenshot_path = COALESCE(
                excluded.screenshot_path,
                test_results.screenshot_path
            )
        """,
        (
            run_id,
            node_id,
            test_name,
            category,
            status,
            duration,
            failure_details,
            screenshot_path,
            datetime.now().isoformat(timespec="seconds")
        )
    )

    connection.commit()
    connection.close()


def finish_test_run(run_id, duration):

    connection = get_results_connection()

    results = connection.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM test_results
        WHERE run_id = ?
        GROUP BY status
        """,
        (run_id,)
    ).fetchall()

    counts = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "error": 0
    }

    for result in results:

        status = result["status"]

        if status in counts:
            counts[status] = result["count"]

    total = sum(counts.values())

    run_status = (
        "passed"
        if counts["failed"] == 0 and counts["error"] == 0
        else "failed"
    )

    connection.execute(
        """
        UPDATE test_runs
        SET
            finished_at = ?,
            duration = ?,
            total = ?,
            passed = ?,
            failed = ?,
            skipped = ?,
            errors = ?,
            status = ?
        WHERE id = ?
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            duration,
            total,
            counts["passed"],
            counts["failed"],
            counts["skipped"],
            counts["error"],
            run_status,
            run_id
        )
    )

    connection.commit()
    connection.close()


def get_recent_runs(limit=10):

    connection = get_results_connection()

    runs = connection.execute(
        """
        SELECT *
        FROM test_runs
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    connection.close()

    return [dict(run) for run in runs]


def get_run_details(run_id):

    connection = get_results_connection()

    run = connection.execute(
        "SELECT * FROM test_runs WHERE id = ?",
        (run_id,)
    ).fetchone()

    results = connection.execute(
        """
        SELECT *
        FROM test_results
        WHERE run_id = ?
        ORDER BY category, test_name
        """,
        (run_id,)
    ).fetchall()

    connection.close()

    return {
        "run": dict(run) if run else None,
        "results": [dict(result) for result in results]
    }


def get_failure_analysis(limit=50):

    connection = get_results_connection()

    failures = connection.execute(
        """
        SELECT
            test_name,
            category,
            failure_details,
            screenshot_path,
            created_at,
            run_id
        FROM test_results
        WHERE status IN ('failed', 'error')
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    connection.close()

    return [dict(failure) for failure in failures]


def compare_test_runs(baseline_run_id, comparison_run_id):

    connection = get_results_connection()

    baseline = connection.execute(
        "SELECT * FROM test_runs WHERE id = ?",
        (baseline_run_id,)
    ).fetchone()

    comparison = connection.execute(
        "SELECT * FROM test_runs WHERE id = ?",
        (comparison_run_id,)
    ).fetchone()

    if baseline is None or comparison is None:
        connection.close()
        return None

    baseline_results = connection.execute(
        """
        SELECT node_id, test_name, category, status, duration
        FROM test_results
        WHERE run_id = ?
        """,
        (baseline_run_id,)
    ).fetchall()

    comparison_results = connection.execute(
        """
        SELECT node_id, test_name, category, status, duration
        FROM test_results
        WHERE run_id = ?
        """,
        (comparison_run_id,)
    ).fetchall()

    connection.close()

    baseline_map = {
        result["node_id"]: dict(result)
        for result in baseline_results
    }

    comparison_map = {
        result["node_id"]: dict(result)
        for result in comparison_results
    }

    newly_failed = []
    fixed_tests = []
    unchanged_failures = []
    new_tests = []

    for node_id, result in comparison_map.items():

        previous = baseline_map.get(node_id)

        if previous is None:

            new_tests.append(result)

        elif (
            result["status"] in ("failed", "error")
            and previous["status"] not in ("failed", "error")
        ):

            newly_failed.append(result)

        elif (
            result["status"] == "passed"
            and previous["status"] in ("failed", "error")
        ):

            fixed_tests.append(result)

        elif (
            result["status"] in ("failed", "error")
            and previous["status"] in ("failed", "error")
        ):

            unchanged_failures.append(result)

    removed_tests = [
        result
        for node_id, result in baseline_map.items()
        if node_id not in comparison_map
    ]

    baseline_pass_rate = (
        round(
            baseline["passed"] / baseline["total"] * 100,
            2
        )
        if baseline["total"] else 0
    )

    comparison_pass_rate = (
        round(
            comparison["passed"] / comparison["total"] * 100,
            2
        )
        if comparison["total"] else 0
    )

    return {
        "baseline": dict(baseline),

        "comparison": dict(comparison),

        "metrics": {
            "pass_rate_change": round(
                comparison_pass_rate - baseline_pass_rate,
                2
            ),

            "duration_change": round(
                comparison["duration"] - baseline["duration"],
                2
            ),

            "test_count_change": (
                comparison["total"] - baseline["total"]
            )
        },

        "changes": {
            "newly_failed": newly_failed,
            "fixed_tests": fixed_tests,
            "unchanged_failures": unchanged_failures,
            "new_tests": new_tests,
            "removed_tests": removed_tests
        }
    }