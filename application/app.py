import os

from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
    request
)

from application.database.db import initialize_database

from application.routes.auth import auth_bp
from application.routes.qa import qa_bp
from application.routes.flasky import flaky_bp
from application.routes.performance import performance_bp
from application.routes.security import security_bp


app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "TESTPILOT_SECRET_KEY",
    "testpilot-development-key"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.getenv("TESTPILOT_COOKIE_SECURE", "false").lower()
        == "true"
    )
)

initialize_database()

app.register_blueprint(auth_bp)
app.register_blueprint(qa_bp)
app.register_blueprint(flaky_bp)
app.register_blueprint(performance_bp)
app.register_blueprint(security_bp)


# --------------------------------------------------
# SECURITY HEADERS
# --------------------------------------------------

@app.after_request
def add_security_headers(response):

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"

    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )

    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https: data: 'unsafe-inline'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )

    return response


# --------------------------------------------------
# QA AND PERFORMANCE AUTHENTICATION
# --------------------------------------------------

@app.before_request
def protect_qa_routes():

    protected_blueprints = {
        "qa",
        "flaky",
        "performance",
        "security"
    }

    if request.blueprint not in protected_blueprints:
        return None

    if "user_id" not in session:

        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": "Authentication required. Please log in."
            }), 401

        return redirect(url_for("login_page"))

    return None


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

@app.route("/login")
def login_page():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# --------------------------------------------------
# REGISTRATION PAGE
# --------------------------------------------------

@app.route("/register")
def register_page():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# --------------------------------------------------
# USER DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login_page"))

    return render_template(
        "dashboard.html",
        username=session.get("username")
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy"
    }), 200


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )