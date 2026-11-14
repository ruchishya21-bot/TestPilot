from flask import Blueprint, render_template, request, jsonify

from utilities.result_store import (
    get_recent_runs,
    get_run_details,
    get_failure_analysis,
    compare_test_runs
)

from utilities.execution_manager import (
    start_execution,
    get_execution_status,
    get_execution_log,
    TEST_SUITES
)


qa_bp = Blueprint("qa", __name__)


# --------------------------------------------------
# QA DASHBOARD
# --------------------------------------------------

@qa_bp.route("/qa")
def dashboard():

    runs = get_recent_runs(limit=20)

    selected_run_id = request.args.get("run_id")

    if selected_run_id:
        details = get_run_details(selected_run_id)

        if details["run"] is None:
            selected_run_id = None

    if not selected_run_id and runs:
        selected_run_id = runs[0]["id"]
        details = get_run_details(selected_run_id)

    elif not selected_run_id:
        details = {
            "run": None,
            "results": []
        }

    selected_run = details["run"]
    test_results = details["results"]

    category_stats = {
        "API": 0,
        "Database": 0,
        "Functional": 0,
        "UI": 0,
        "Other": 0
    }

    for result in test_results:

        category = result["category"]

        if category in category_stats:
            category_stats[category] += 1

    total = selected_run["total"] if selected_run else 0
    passed = selected_run["passed"] if selected_run else 0

    pass_rate = (
        round((passed / total) * 100, 1)
        if total > 0
        else 0
    )

    return render_template(
        "qa_dashboard.html",
        runs=runs,
        selected_run=selected_run,
        test_results=test_results,
        category_stats=category_stats,
        pass_rate=pass_rate,
        test_suites=TEST_SUITES
    )


# --------------------------------------------------
# RUN COMPARISON PAGE
# --------------------------------------------------

@qa_bp.route("/qa/compare")
def run_comparison_page():

    return render_template("run_comparison.html")


# --------------------------------------------------
# START TEST EXECUTION
# --------------------------------------------------

@qa_bp.route("/api/qa/start", methods=["POST"])
def start_test_execution():

    data = request.get_json(silent=True) or {}

    test_type = data.get("test_type", "all")

    try:

        state = start_execution(test_type)

        return jsonify({
            "success": True,
            "message": "Test execution started successfully.",
            "execution": state
        }), 202

    except ValueError as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    except RuntimeError as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 409

    except Exception as error:

        return jsonify({
            "success": False,
            "message": f"Unable to start execution: {error}"
        }), 500


# --------------------------------------------------
# EXECUTION STATUS
# --------------------------------------------------

@qa_bp.route("/api/qa/status", methods=["GET"])
def test_execution_status():

    return jsonify({
        "success": True,
        "execution": get_execution_status()
    })


# --------------------------------------------------
# EXECUTION LOGS
# --------------------------------------------------

@qa_bp.route("/api/qa/logs", methods=["GET"])
def test_execution_logs():

    return jsonify({
        "success": True,
        "logs": get_execution_log()
    })


# --------------------------------------------------
# AVAILABLE TEST SUITES
# --------------------------------------------------

@qa_bp.route("/api/qa/suites", methods=["GET"])
def available_test_suites():

    return jsonify({
        "success": True,
        "suites": TEST_SUITES
    })


# --------------------------------------------------
# ADVANCED QA ANALYTICS API
# --------------------------------------------------

@qa_bp.route("/api/qa/analytics", methods=["GET"])
def qa_analytics():

    try:

        runs = get_recent_runs(limit=50)

        total_runs = len(runs)

        total_tests = sum(run["total"] for run in runs)

        total_passed = sum(run["passed"] for run in runs)

        total_failed = sum(run["failed"] for run in runs)

        total_skipped = sum(run["skipped"] for run in runs)

        total_errors = sum(run["errors"] for run in runs)

        overall_pass_rate = (
            round((total_passed / total_tests) * 100, 2)
            if total_tests > 0
            else 0
        )

        execution_trends = []

        for run in reversed(runs):

            execution_trends.append({

                "run_id": run["id"][:8],

                "started_at": run["started_at"],

                "total": run["total"],

                "passed": run["passed"],

                "failed": run["failed"],

                "skipped": run["skipped"],

                "errors": run["errors"],

                "duration": round(run["duration"], 2),

                "pass_rate": (
                    round(
                        (run["passed"] / run["total"]) * 100,
                        2
                    )
                    if run["total"] > 0
                    else 0
                ),

                "status": run["status"]

            })

        category_distribution = {
            "API": 0,
            "Database": 0,
            "Functional": 0,
            "UI": 0,
            "Other": 0
        }

        for run in runs:

            details = get_run_details(run["id"])

            for result in details["results"]:

                category = result["category"]

                if category in category_distribution:
                    category_distribution[category] += 1

        return jsonify({

            "success": True,

            "summary": {

                "total_runs": total_runs,

                "total_tests": total_tests,

                "passed": total_passed,

                "failed": total_failed,

                "skipped": total_skipped,

                "errors": total_errors,

                "pass_rate": overall_pass_rate

            },

            "execution_trends": execution_trends,

            "category_distribution": category_distribution

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "message": f"Unable to generate analytics: {error}"

        }), 500


# --------------------------------------------------
# FAILURE ANALYSIS API
# --------------------------------------------------

@qa_bp.route("/api/qa/failures", methods=["GET"])
def qa_failures():

    try:

        failures = get_failure_analysis(limit=50)

        return jsonify({

            "success": True,

            "total_failures": len(failures),

            "failures": failures

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "message": f"Unable to retrieve failure analysis: {error}"

        }), 500


# --------------------------------------------------
# TEST RUN COMPARISON API
# --------------------------------------------------

@qa_bp.route("/api/qa/compare", methods=["GET"])
def compare_runs():

    baseline_id = request.args.get("baseline")
    comparison_id = request.args.get("comparison")

    if not baseline_id or not comparison_id:

        return jsonify({

            "success": False,

            "message": "Both baseline and comparison run IDs are required."

        }), 400

    if baseline_id == comparison_id:

        return jsonify({

            "success": False,

            "message": "Please select two different test runs."

        }), 400

    try:

        comparison = compare_test_runs(
            baseline_id,
            comparison_id
        )

        if comparison is None:

            return jsonify({

                "success": False,

                "message": "One or both test runs were not found."

            }), 404

        return jsonify({

            "success": True,

            "comparison": comparison

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "message": f"Unable to compare test runs: {error}"

        }), 500


# --------------------------------------------------
# HISTORICAL TEST RUNS API
# --------------------------------------------------

@qa_bp.route("/api/qa/runs", methods=["GET"])
def get_test_runs():

    try:

        runs = get_recent_runs(limit=50)

        return jsonify({

            "success": True,

            "total_runs": len(runs),

            "runs": runs

        }), 200

    except Exception as error:

        return jsonify({

            "success": False,

            "message": f"Unable to retrieve test runs: {error}"

        }), 500