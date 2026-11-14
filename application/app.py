from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    url_for,
    session
)

from application.database.db import initialize_database

from application.routes.auth import auth_bp
from application.routes.qa import qa_bp
from application.routes.flasky import flaky_bp
from application.routes.performance import performance_bp


app = Flask(__name__)

app.config["SECRET_KEY"] = "testpilot-development-key"

initialize_database()

app.register_blueprint(auth_bp)
app.register_blueprint(qa_bp)
app.register_blueprint(flaky_bp)
app.register_blueprint(performance_bp)


@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/login")
def login_page():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register")
def register_page():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login_page"))

    return render_template(
        "dashboard.html",
        username=session.get("username")
    )


@app.route("/health")
def health():

    return jsonify({
        "status": "healthy"
    }), 200


if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )