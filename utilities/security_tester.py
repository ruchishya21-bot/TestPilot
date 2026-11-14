import uuid
from datetime import datetime
from urllib.parse import urlparse

import requests

from config.target_config import TargetConfig
from utilities.result_store import get_results_connection


# --------------------------------------------------
# SECURITY SCANNER CONFIGURATION
# --------------------------------------------------

SECURITY_TIMEOUT = min(TargetConfig.REQUEST_TIMEOUT, 10)

SECURITY_HEADERS = {
    "Content-Security-Policy": "Content Security Policy",
    "X-Content-Type-Options": "MIME type protection",
    "X-Frame-Options": "Clickjacking protection",
    "Referrer-Policy": "Referrer policy",
    "Permissions-Policy": "Browser permissions policy"
}

SENSITIVE_PATHS = [
    "/.env",
    "/.git/HEAD",
    "/config.py",
    "/__debugger__",
    "/server-status"
]

QA_API_PATHS = [
    "/api/qa/start",
    "/api/qa/status",
    "/api/qa/logs",
    "/api/qa/analytics",
    "/api/qa/runs",
    "/api/performance/history",
    "/api/performance/stats"
]

SQLI_PAYLOAD = "' OR '1'='1"

XSS_PAYLOAD = "<script>alert('testpilot')</script>"

SQL_ERROR_SIGNATURES = [
    "sqlite error",
    "sql syntax",
    "sqlite3.operationalerror",
    "mysql syntax",
    "postgresql error",
    "unclosed quotation mark"
]


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def initialize_security_database():

    connection = get_results_connection()

    try:

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS security_scans (
                id TEXT PRIMARY KEY,
                application TEXT NOT NULL,
                base_url TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                total_checks INTEGER DEFAULT 0,
                passed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                not_assessed INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running'
            );

            CREATE TABLE IF NOT EXISTS security_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT,
                recommendation TEXT,
                endpoint TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (scan_id)
                    REFERENCES security_scans(id)
            );
        """)

        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(security_scans)"
            ).fetchall()
        }

        if "not_assessed" not in columns:

            connection.execute("""
                ALTER TABLE security_scans
                ADD COLUMN not_assessed INTEGER DEFAULT 0
            """)

        connection.commit()

    finally:

        connection.close()


# --------------------------------------------------
# FINDING MANAGEMENT
# --------------------------------------------------

def create_finding(
    category,
    title,
    severity,
    status,
    description,
    recommendation,
    endpoint=None
):

    return {
        "category": category,
        "title": title,
        "severity": severity,
        "status": status,
        "description": description,
        "recommendation": recommendation,
        "endpoint": endpoint
    }


def save_security_scan(scan, findings):

    connection = get_results_connection()

    try:

        connection.execute(
            """
            INSERT INTO security_scans (
                id,
                application,
                base_url,
                started_at,
                finished_at,
                total_checks,
                passed,
                failed,
                warnings,
                not_assessed,
                risk_score,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan["id"],
                scan["application"],
                scan["base_url"],
                scan["started_at"],
                scan["finished_at"],
                scan["total_checks"],
                scan["passed"],
                scan["failed"],
                scan["warnings"],
                scan["not_assessed"],
                scan["risk_score"],
                scan["status"]
            )
        )

        for finding in findings:

            connection.execute(
                """
                INSERT INTO security_findings (
                    scan_id,
                    category,
                    title,
                    severity,
                    status,
                    description,
                    recommendation,
                    endpoint,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan["id"],
                    finding["category"],
                    finding["title"],
                    finding["severity"],
                    finding["status"],
                    finding["description"],
                    finding["recommendation"],
                    finding["endpoint"],
                    datetime.now().isoformat()
                )
            )

        connection.commit()

    finally:

        connection.close()


# --------------------------------------------------
# SECURITY CHECK: RESPONSE HEADERS
# --------------------------------------------------

def check_security_headers(response):

    findings = []

    for header, description in SECURITY_HEADERS.items():

        if header not in response.headers:

            findings.append(
                create_finding(
                    "Security Headers",
                    f"Missing {header}",
                    "Medium",
                    "Failed",
                    f"{description} header is missing.",
                    f"Configure the {header} response header.",
                    response.url
                )
            )

        else:

            findings.append(
                create_finding(
                    "Security Headers",
                    f"{header} configured",
                    "Info",
                    "Passed",
                    f"{description} header is present.",
                    "Continue reviewing its configuration.",
                    response.url
                )
            )

    # HSTS is meaningful only over HTTPS.

    if urlparse(response.url).scheme == "https":

        if "Strict-Transport-Security" not in response.headers:

            findings.append(
                create_finding(
                    "Security Headers",
                    "Missing Strict-Transport-Security",
                    "Medium",
                    "Failed",
                    "HTTPS response does not contain an HSTS header.",
                    "Configure Strict-Transport-Security.",
                    response.url
                )
            )

    return findings


# --------------------------------------------------
# SECURITY CHECK: SESSION COOKIES
# --------------------------------------------------

def check_cookie_security(response):

    findings = []

    cookies = response.headers.get("Set-Cookie", "")

    if not cookies:

        findings.append(
            create_finding(
                "Cookie Security",
                "Session cookie attributes not assessed",
                "Info",
                "Not Assessed",
                "The inspected health endpoint did not issue a session cookie. "
                "Cookie security attributes could not be evaluated.",
                "Inspect an authenticated response that issues a session "
                "cookie to verify HttpOnly, Secure, and SameSite attributes.",
                response.url
            )
        )

        return findings

    cookie_lower = cookies.lower()

    checks = {
        "HttpOnly": "httponly",
        "Secure": "secure",
        "SameSite": "samesite"
    }

    for name, attribute in checks.items():

        if attribute not in cookie_lower:

            findings.append(
                create_finding(
                    "Cookie Security",
                    f"Missing {name} cookie attribute",
                    "Medium",
                    "Failed",
                    f"Cookie does not contain the {name} attribute.",
                    f"Configure the {name} attribute on session cookies.",
                    response.url
                )
            )

        else:

            findings.append(
                create_finding(
                    "Cookie Security",
                    f"{name} attribute configured",
                    "Info",
                    "Passed",
                    f"Cookie contains the {name} attribute.",
                    "Continue reviewing cookie configuration.",
                    response.url
                )
            )

    return findings

    cookie_lower = cookies.lower()

    checks = {
        "HttpOnly": "httponly",
        "Secure": "secure",
        "SameSite": "samesite"
    }

    for name, attribute in checks.items():

        if attribute not in cookie_lower:

            findings.append(
                create_finding(
                    "Cookie Security",
                    f"Missing {name} cookie attribute",
                    "Medium",
                    "Failed",
                    f"Cookie does not contain the {name} attribute.",
                    f"Configure the {name} attribute on session cookies.",
                    response.url
                )
            )

        else:

            findings.append(
                create_finding(
                    "Cookie Security",
                    f"{name} attribute configured",
                    "Info",
                    "Passed",
                    f"Cookie contains the {name} attribute.",
                    "Continue reviewing cookie configuration.",
                    response.url
                )
            )

    return findings


# --------------------------------------------------
# SECURITY CHECK: AUTHENTICATION
# --------------------------------------------------

def check_authentication(session):

    findings = []

    try:

        response = session.get(
            TargetConfig.get_url("/dashboard"),
            timeout=SECURITY_TIMEOUT,
            allow_redirects=False
        )

        if response.status_code in (301, 302, 303, 307, 308):

            location = response.headers.get("Location", "")

            if "login" in location.lower():

                findings.append(
                    create_finding(
                        "Authentication",
                        "Dashboard authentication enforced",
                        "Info",
                        "Passed",
                        "Unauthenticated dashboard access redirects to login.",
                        "Continue protecting authenticated application pages.",
                        "/dashboard"
                    )
                )

            else:

                findings.append(
                    create_finding(
                        "Authentication",
                        "Unexpected dashboard redirect",
                        "Low",
                        "Warning",
                        "Dashboard redirected without an identifiable login destination.",
                        "Review dashboard authentication behavior.",
                        "/dashboard"
                    )
                )

        elif response.status_code == 401:

            findings.append(
                create_finding(
                    "Authentication",
                    "Dashboard access rejected",
                    "Info",
                    "Passed",
                    "Unauthenticated access was rejected.",
                    "Continue enforcing authentication.",
                    "/dashboard"
                )
            )

        else:

            findings.append(
                create_finding(
                    "Authentication",
                    "Dashboard may be accessible without authentication",
                    "High",
                    "Failed",
                    f"Unauthenticated dashboard request returned HTTP {response.status_code}.",
                    "Require authentication before rendering the dashboard.",
                    "/dashboard"
                )
            )

    except requests.RequestException as error:

        findings.append(
            create_finding(
                "Authentication",
                "Dashboard authentication check failed",
                "Low",
                "Warning",
                str(error),
                "Verify that the configured target is reachable.",
                "/dashboard"
            )
        )

    return findings


# --------------------------------------------------
# SECURITY CHECK: UNAUTHENTICATED QA APIS
# --------------------------------------------------

def check_api_exposure(session):

    findings = []

    for endpoint in QA_API_PATHS:

        try:

            response = session.get(
                TargetConfig.get_url(endpoint),
                timeout=SECURITY_TIMEOUT,
                allow_redirects=False
            )

            if response.status_code == 200:

                findings.append(
                    create_finding(
                        "Access Control",
                        "QA API accessible without authentication",
                        "Medium",
                        "Warning",
                        f"{endpoint} returned HTTP 200 without an authenticated session.",
                        "Determine whether this endpoint should be public. "
                        "Protect sensitive QA operations and execution data "
                        "with authentication and authorization.",
                        endpoint
                    )
                )

            elif response.status_code in (401, 403):

                findings.append(
                    create_finding(
                        "Access Control",
                        "QA API access restricted",
                        "Info",
                        "Passed",
                        f"{endpoint} rejected unauthenticated access.",
                        "Continue enforcing appropriate authorization.",
                        endpoint
                    )
                )

        except requests.RequestException:

            findings.append(
                create_finding(
                    "Access Control",
                    "QA API check could not complete",
                    "Low",
                    "Warning",
                    f"Could not inspect {endpoint}.",
                    "Verify target availability.",
                    endpoint
                )
            )

    return findings


# --------------------------------------------------
# SECURITY CHECK: SENSITIVE FILE EXPOSURE
# --------------------------------------------------

def check_sensitive_files(session):

    findings = []

    for endpoint in SENSITIVE_PATHS:

        try:

            response = session.get(
                TargetConfig.get_url(endpoint),
                timeout=SECURITY_TIMEOUT,
                allow_redirects=False
            )

            if response.status_code == 200:

                findings.append(
                    create_finding(
                        "Information Disclosure",
                        "Potential sensitive file exposure",
                        "High",
                        "Failed",
                        f"{endpoint} returned HTTP 200.",
                        "Verify that sensitive files are not publicly accessible.",
                        endpoint
                    )
                )

            else:

                findings.append(
                    create_finding(
                        "Information Disclosure",
                        "Sensitive file not directly accessible",
                        "Info",
                        "Passed",
                        f"{endpoint} returned HTTP {response.status_code}.",
                        "Continue restricting access to configuration files.",
                        endpoint
                    )
                )

        except requests.RequestException:

            findings.append(
                create_finding(
                    "Information Disclosure",
                    "Sensitive file check incomplete",
                    "Low",
                    "Warning",
                    f"Could not inspect {endpoint}.",
                    "Verify target availability.",
                    endpoint
                )
            )

    return findings


# --------------------------------------------------
# SECURITY CHECK: SQL INJECTION INDICATORS
# --------------------------------------------------

def check_sql_injection(session):

    findings = []

    try:

        response = session.post(
            TargetConfig.get_url("/api/auth/login"),
            json={
                "email": SQLI_PAYLOAD,
                "password": "invalid-testpilot-password"
            },
            timeout=SECURITY_TIMEOUT,
            allow_redirects=False
        )

        body = response.text.lower()

        sql_errors = [
            signature
            for signature in SQL_ERROR_SIGNATURES
            if signature in body
        ]

        if sql_errors:

            findings.append(
                create_finding(
                    "SQL Injection",
                    "Potential SQL error disclosure",
                    "High",
                    "Failed",
                    "The authentication response contains a database error signature.",
                    "Use parameterized queries and avoid exposing database errors.",
                    "/api/auth/login"
                )
            )

        elif response.status_code == 401:

            findings.append(
                create_finding(
                    "SQL Injection",
                    "SQL injection probe rejected",
                    "Info",
                    "Passed",
                    "The harmless authentication probe was rejected without a database error.",
                    "Continue using parameterized database queries. "
                    "This check does not prove the absence of SQL injection.",
                    "/api/auth/login"
                )
            )

        else:

            findings.append(
                create_finding(
                    "SQL Injection",
                    "Unexpected authentication response",
                    "Low",
                    "Warning",
                    f"Probe returned HTTP {response.status_code}.",
                    "Review authentication input handling manually.",
                    "/api/auth/login"
                )
            )

    except requests.RequestException as error:

        findings.append(
            create_finding(
                "SQL Injection",
                "SQL injection check incomplete",
                "Low",
                "Warning",
                str(error),
                "Verify target availability.",
                "/api/auth/login"
            )
        )

    return findings


# --------------------------------------------------
# SECURITY CHECK: XSS REFLECTION
# --------------------------------------------------

def check_xss(session):

    findings = []

    try:

        response = session.get(
            TargetConfig.get_url("/login"),
            params={
                "testpilot_input": XSS_PAYLOAD
            },
            timeout=SECURITY_TIMEOUT,
            allow_redirects=False
        )

        if XSS_PAYLOAD in response.text:

            findings.append(
                create_finding(
                    "Cross-Site Scripting",
                    "Potential reflected XSS",
                    "Medium",
                    "Failed",
                    "The test payload was reflected without being encoded.",
                    "Apply context-aware output encoding and validate untrusted input.",
                    "/login"
                )
            )

        else:

            findings.append(
                create_finding(
                    "Cross-Site Scripting",
                    "XSS reflection not detected",
                    "Info",
                    "Passed",
                    "The test payload was not reflected in the login response.",
                    "Continue applying output encoding. "
                    "This check does not prove the absence of XSS.",
                    "/login"
                )
            )

    except requests.RequestException as error:

        findings.append(
            create_finding(
                "Cross-Site Scripting",
                "XSS check incomplete",
                "Low",
                "Warning",
                str(error),
                "Verify target availability.",
                "/login"
            )
        )

    return findings


# --------------------------------------------------
# SECURITY RISK SCORING
# --------------------------------------------------

def calculate_risk_score(findings):

    weights = {
        "Critical": 40,
        "High": 25,
        "Medium": 10,
        "Low": 5,
        "Info": 0
    }

    score = sum(
        weights.get(item["severity"], 0)
        for item in findings
        if item["status"] in ("Failed", "Warning")
    )

    return min(score, 100)


# --------------------------------------------------
# MAIN SECURITY SCAN
# --------------------------------------------------

def run_security_scan():

    initialize_security_database()

    scan_id = str(uuid.uuid4())

    started_at = datetime.now().isoformat()

    scan = {
        "id": scan_id,
        "application": TargetConfig.APP_NAME,
        "base_url": TargetConfig.BASE_URL,
        "started_at": started_at,
        "finished_at": None,
        "total_checks": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "not_assessed": 0,
        "risk_score": 0,
        "status": "running"
    }

    findings = []

    parsed_url = urlparse(TargetConfig.BASE_URL)

    if (
        parsed_url.scheme not in ("http", "https")
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
    ):

        raise ValueError(
            "Configured target URL is invalid."
        )

    session = requests.Session()

    try:

        response = session.get(
            TargetConfig.get_health_url(),
            timeout=SECURITY_TIMEOUT
        )

        if not response.ok:

            raise RuntimeError(
                f"Target health check failed: HTTP {response.status_code}"
            )

        findings.extend(check_security_headers(response))
        findings.extend(check_cookie_security(response))
        findings.extend(check_authentication(session))
        findings.extend(check_api_exposure(session))
        findings.extend(check_sensitive_files(session))
        findings.extend(check_sql_injection(session))
        findings.extend(check_xss(session))

        scan["total_checks"] = len(findings)

        scan["passed"] = sum(
            item["status"] == "Passed"
            for item in findings
        )

        scan["failed"] = sum(
            item["status"] == "Failed"
            for item in findings
        )

        scan["warnings"] = sum(
            item["status"] == "Warning"
            for item in findings
        )

        scan["not_assessed"] = sum(
            item["status"] == "Not Assessed"
            for item in findings
        )

        scan["risk_score"] = calculate_risk_score(
            findings
        )

        scan["status"] = "completed"

    except Exception:

        scan["status"] = "failed"

        raise

    finally:

        session.close()

        scan["finished_at"] = datetime.now().isoformat()

        save_security_scan(
            scan,
            findings
        )

    return {
        **scan,
        "findings": findings
    }


# --------------------------------------------------
# SECURITY SCAN HISTORY
# --------------------------------------------------

def get_security_history(limit=20):

    limit = max(1, min(int(limit), 100))

    initialize_security_database()

    connection = get_results_connection()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM security_scans
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:

        connection.close()


# --------------------------------------------------
# SECURITY FINDINGS HISTORY
# --------------------------------------------------

def get_security_findings(scan_id=None, limit=100):

    limit = max(1, min(int(limit), 500))

    initialize_security_database()

    connection = get_results_connection()

    try:

        if scan_id:

            rows = connection.execute(
                """
                SELECT *
                FROM security_findings
                WHERE scan_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (scan_id, limit)
            ).fetchall()

        else:

            rows = connection.execute(
                """
                SELECT *
                FROM security_findings
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [dict(row) for row in rows]

    finally:

        connection.close()