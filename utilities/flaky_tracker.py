import sqlite3

from utilities.result_store import get_results_connection


def initialize_flaky_database():
    connection = get_results_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS flaky_test_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            node_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            retry_count INTEGER NOT NULL,
            final_status TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            UNIQUE(run_id, node_id)
        )
        """
    )

    connection.commit()
    connection.close()


def record_flaky_test(run_id, node_id, retry_count):
    if not run_id or retry_count <= 0:
        return

    connection = get_results_connection()

    connection.execute(
        """
        INSERT INTO flaky_test_history (
            run_id,
            node_id,
            test_name,
            retry_count,
            final_status,
            detected_at
        )
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(run_id, node_id)
        DO UPDATE SET
            retry_count = excluded.retry_count,
            final_status = excluded.final_status,
            detected_at = excluded.detected_at
        """,
        (
            run_id,
            node_id,
            node_id.split("::")[-1],
            retry_count,
            "passed"
        )
    )

    connection.commit()
    connection.close()


def get_flaky_test_history(limit=50):
    connection = get_results_connection()

    records = connection.execute(
        """
        SELECT *
        FROM flaky_test_history
        ORDER BY detected_at DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    connection.close()

    return [dict(record) for record in records]


def get_flaky_test_stats():
    connection = get_results_connection()

    stats = connection.execute(
        """
        SELECT
            COUNT(*) AS flaky_tests,
            COALESCE(SUM(retry_count), 0) AS total_retries
        FROM flaky_test_history
        """
    ).fetchone()

    connection.close()

    return dict(stats)