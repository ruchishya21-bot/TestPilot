import json
import sqlite3
import time
import uuid

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

from config.target_config import TargetConfig
from utilities.result_store import get_results_connection
from utilities.target_validator import validate_target


# --------------------------------------------------
# PERFORMANCE DATABASE
# --------------------------------------------------

def initialize_performance_database():

    connection = get_results_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS performance_runs (
            id TEXT PRIMARY KEY,
            endpoint TEXT NOT NULL,
            total_requests INTEGER NOT NULL,
            concurrency INTEGER NOT NULL,
            successful_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            average_response_time REAL DEFAULT 0,
            min_response_time REAL DEFAULT 0,
            max_response_time REAL DEFAULT 0,
            p50_response_time REAL DEFAULT 0,
            p95_response_time REAL DEFAULT 0,
            p99_response_time REAL DEFAULT 0,
            requests_per_second REAL DEFAULT 0,
            total_duration REAL DEFAULT 0,
            status_codes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# --------------------------------------------------
# SINGLE HTTP REQUEST
# --------------------------------------------------

def execute_request(url):

    start_time = time.perf_counter()

    try:

        response = requests.get(
            url,
            timeout=TargetConfig.REQUEST_TIMEOUT
        )

        duration = (
            time.perf_counter() - start_time
        ) * 1000

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "response_time": round(duration, 2),
            "error": None
        }

    except requests.exceptions.RequestException as error:

        duration = (
            time.perf_counter() - start_time
        ) * 1000

        return {
            "success": False,
            "status_code": None,
            "response_time": round(duration, 2),
            "error": str(error)
        }


# --------------------------------------------------
# PERCENTILE CALCULATION
# --------------------------------------------------

def calculate_percentile(values, percentile):

    if not values:
        return 0

    sorted_values = sorted(values)

    index = round(
        (percentile / 100) * (len(sorted_values) - 1)
    )

    return round(sorted_values[index], 2)


# --------------------------------------------------
# RUN PERFORMANCE TEST
# --------------------------------------------------

def run_performance_test(
    endpoint="/health",
    total_requests=50,
    concurrency=5
):

    # Validate request limits.

    if not isinstance(total_requests, int) or not 1 <= total_requests <= 500:
        raise ValueError(
            "Total requests must be between 1 and 500."
        )

    if not isinstance(concurrency, int) or not 1 <= concurrency <= 25:
        raise ValueError(
            "Concurrency must be between 1 and 25."
        )

    if concurrency > total_requests:
        concurrency = total_requests

    if (
        not isinstance(endpoint, str)
        or not endpoint.startswith("/")
        or endpoint.startswith("//")
        or "://" in endpoint
    ):
        raise ValueError(
            "Endpoint must be a relative path beginning with /."
        )

    # Validate target before sending requests.

    validation = validate_target()

    if not validation["healthy"]:
        raise RuntimeError(
            "Target application is not healthy. "
            + str(validation["message"])
        )

    url = TargetConfig.get_url(endpoint)

    run_id = str(uuid.uuid4())

    response_times = []
    successful_requests = 0
    failed_requests = 0
    status_codes = {}

    start_time = time.perf_counter()

    # Execute controlled concurrent requests.

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        futures = [
            executor.submit(execute_request, url)
            for _ in range(total_requests)
        ]

        for future in as_completed(futures):

            result = future.result()

            response_times.append(
                result["response_time"]
            )

            if result["success"]:

                successful_requests += 1

            else:

                failed_requests += 1

            status = result["status_code"]

            if status is not None:

                status_codes[str(status)] = (
                    status_codes.get(str(status), 0) + 1
                )

    total_duration = (
        time.perf_counter() - start_time
    )

    # Calculate performance metrics.

    average_time = (
        sum(response_times) / len(response_times)
        if response_times else 0
    )

    min_time = (
        min(response_times)
        if response_times else 0
    )

    max_time = (
        max(response_times)
        if response_times else 0
    )

    requests_per_second = (
        total_requests / total_duration
        if total_duration > 0 else 0
    )

    metrics = {
        "id": run_id,
        "endpoint": endpoint,
        "total_requests": total_requests,
        "concurrency": concurrency,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "average_response_time": round(average_time, 2),
        "min_response_time": round(min_time, 2),
        "max_response_time": round(max_time, 2),
        "p50_response_time": calculate_percentile(
            response_times, 50
        ),
        "p95_response_time": calculate_percentile(
            response_times, 95
        ),
        "p99_response_time": calculate_percentile(
            response_times, 99
        ),
        "requests_per_second": round(
            requests_per_second, 2
        ),
        "total_duration": round(total_duration, 2),
        "status_codes": status_codes,
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        )
    }

    # Save results in SQLite.

    initialize_performance_database()

    connection = get_results_connection()

    connection.execute(
        """
        INSERT INTO performance_runs (
            id,
            endpoint,
            total_requests,
            concurrency,
            successful_requests,
            failed_requests,
            average_response_time,
            min_response_time,
            max_response_time,
            p50_response_time,
            p95_response_time,
            p99_response_time,
            requests_per_second,
            total_duration,
            status_codes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metrics["id"],
            metrics["endpoint"],
            metrics["total_requests"],
            metrics["concurrency"],
            metrics["successful_requests"],
            metrics["failed_requests"],
            metrics["average_response_time"],
            metrics["min_response_time"],
            metrics["max_response_time"],
            metrics["p50_response_time"],
            metrics["p95_response_time"],
            metrics["p99_response_time"],
            metrics["requests_per_second"],
            metrics["total_duration"],
            json.dumps(status_codes),
            metrics["created_at"]
        )
    )

    connection.commit()
    connection.close()

    return metrics


# --------------------------------------------------
# PERFORMANCE HISTORY
# --------------------------------------------------

def get_performance_history(limit=20):

    initialize_performance_database()

    connection = get_results_connection()

    records = connection.execute(
        """
        SELECT *
        FROM performance_runs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    connection.close()

    history = []

    for record in records:

        item = dict(record)

        item["status_codes"] = json.loads(
            item["status_codes"] or "{}"
        )

        history.append(item)

    return history