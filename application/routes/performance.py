from flask import Blueprint, request, jsonify, render_template

from utilities.performance_tester import (
    run_performance_test,
    get_performance_history,
    initialize_performance_database
)


performance_bp = Blueprint(
    "performance",
    __name__
)


# --------------------------------------------------
# PERFORMANCE DASHBOARD
# --------------------------------------------------

@performance_bp.route("/qa/performance")
def performance_dashboard():

    return render_template("performance_dashboard.html")


# --------------------------------------------------
# PERFORMANCE TEST EXECUTION
# --------------------------------------------------

@performance_bp.route(
    "/api/performance/run",
    methods=["POST"]
)
def run_performance():

    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Request body must be a JSON object."
        }), 400

    endpoint = data.get("endpoint", "/health")
    total_requests = data.get("total_requests", 50)
    concurrency = data.get("concurrency", 5)

    try:

        if (
            isinstance(total_requests, bool)
            or not isinstance(total_requests, int)
        ):
            raise ValueError(
                "total_requests must be an integer."
            )

        if (
            isinstance(concurrency, bool)
            or not isinstance(concurrency, int)
        ):
            raise ValueError(
                "concurrency must be an integer."
            )

        results = run_performance_test(
            endpoint=endpoint,
            total_requests=total_requests,
            concurrency=concurrency
        )

        return jsonify({
            "success": True,
            "message": "Performance test completed successfully.",
            "results": results
        }), 200

    except ValueError as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except RuntimeError as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 503

    except Exception:

        return jsonify({
            "success": False,
            "error": "Performance test could not be completed."
        }), 500


# --------------------------------------------------
# PERFORMANCE HISTORY
# --------------------------------------------------

@performance_bp.route(
    "/api/performance/history",
    methods=["GET"]
)
def performance_history():

    try:

        limit = request.args.get(
            "limit",
            default=20,
            type=int
        )

        if not 1 <= limit <= 100:
            return jsonify({
                "success": False,
                "error": "Limit must be between 1 and 100."
            }), 400

        history = get_performance_history(
            limit=limit
        )

        return jsonify({
            "success": True,
            "total_runs": len(history),
            "history": history
        }), 200

    except Exception:

        return jsonify({
            "success": False,
            "error": "Unable to retrieve performance history."
        }), 500


# --------------------------------------------------
# PERFORMANCE STATISTICS
# --------------------------------------------------

@performance_bp.route(
    "/api/performance/stats",
    methods=["GET"]
)
def performance_stats():

    try:

        initialize_performance_database()

        history = get_performance_history(
            limit=100
        )

        total_runs = len(history)

        total_requests = sum(
            item["total_requests"]
            for item in history
        )

        successful_requests = sum(
            item["successful_requests"]
            for item in history
        )

        failed_requests = sum(
            item["failed_requests"]
            for item in history
        )

        average_response_time = (
            sum(
                item["average_response_time"]
                for item in history
            ) / total_runs
            if total_runs else 0
        )

        average_throughput = (
            sum(
                item["requests_per_second"]
                for item in history
            ) / total_runs
            if total_runs else 0
        )

        return jsonify({
            "success": True,
            "stats": {
                "total_runs": total_runs,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "average_response_time": round(
                    average_response_time, 2
                ),
                "average_throughput": round(
                    average_throughput, 2
                )
            }
        }), 200

    except Exception:

        return jsonify({
            "success": False,
            "error": "Unable to calculate performance statistics."
        }), 500