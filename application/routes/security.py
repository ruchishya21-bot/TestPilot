from flask import Blueprint, request, jsonify, render_template

from utilities.security_tester import (
    run_security_scan,
    get_security_history,
    get_security_findings,
    initialize_security_database
)


security_bp = Blueprint(
    "security",
    __name__
)


# --------------------------------------------------
# SECURITY DASHBOARD
# --------------------------------------------------

@security_bp.route("/qa/security")
def security_dashboard():

    return render_template("security_dashboard.html")


# --------------------------------------------------
# EXECUTE SECURITY SCAN
# --------------------------------------------------

@security_bp.route(
    "/api/security/scan",
    methods=["POST"]
)
def execute_security_scan():

    try:

        results = run_security_scan()

        return jsonify({
            "success": True,
            "message": "Security scan completed successfully.",
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
            "error": "Security scan could not be completed."
        }), 500


# --------------------------------------------------
# SECURITY SCAN HISTORY
# --------------------------------------------------

@security_bp.route(
    "/api/security/history",
    methods=["GET"]
)
def security_history():

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

        history = get_security_history(
            limit=limit
        )

        return jsonify({
            "success": True,
            "total_scans": len(history),
            "history": history
        }), 200

    except Exception:

        return jsonify({
            "success": False,
            "error": "Unable to retrieve security scan history."
        }), 500


# --------------------------------------------------
# SECURITY FINDINGS
# --------------------------------------------------

@security_bp.route(
    "/api/security/findings",
    methods=["GET"]
)
def security_findings():

    try:

        scan_id = request.args.get("scan_id")

        limit = request.args.get(
            "limit",
            default=100,
            type=int
        )

        if not 1 <= limit <= 500:

            return jsonify({
                "success": False,
                "error": "Limit must be between 1 and 500."
            }), 400

        findings = get_security_findings(
            scan_id=scan_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "total_findings": len(findings),
            "findings": findings
        }), 200

    except Exception:

        return jsonify({
            "success": False,
            "error": "Unable to retrieve security findings."
        }), 500


# --------------------------------------------------
# SECURITY STATISTICS
# --------------------------------------------------

@security_bp.route("/api/security/stats", methods=["GET"])
def security_stats():
    try:
        initialize_security_database()
        history = get_security_history(limit=100)

        total_scans = len(history)

        completed_scans = [
            scan for scan in history
            if scan["status"] == "completed"
        ]

        total_checks = sum(scan["total_checks"] for scan in history)
        total_passed = sum(scan["passed"] for scan in history)
        total_failed = sum(scan["failed"] for scan in history)
        total_warnings = sum(scan["warnings"] for scan in history)
        total_not_assessed = sum(
            scan.get("not_assessed", 0) for scan in history
        )

        average_risk_score = (
            sum(scan["risk_score"] for scan in completed_scans)
            / len(completed_scans)
            if completed_scans else 0
        )

        latest_scan = history[0] if history else None

        return jsonify({
            "success": True,
            "stats": {
                "total_scans": total_scans,
                "completed_scans": len(completed_scans),
                "total_checks": total_checks,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_warnings": total_warnings,
                "total_not_assessed": total_not_assessed,
                "average_risk_score": round(average_risk_score, 2),
                "latest_risk_score": (
                    latest_scan["risk_score"] if latest_scan else 0
                ),
                "latest_scan_status": (
                    latest_scan["status"]
                    if latest_scan else "No scans yet"
                ),
                "latest_not_assessed": (
                    latest_scan.get("not_assessed", 0)
                    if latest_scan else 0
                )
            }
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "error": "Unable to calculate security statistics."
        }), 500