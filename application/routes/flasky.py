from flask import Blueprint, render_template

flaky_bp = Blueprint("flaky", __name__)


@flaky_bp.route("/qa/flaky")
def flaky_dashboard():

    return render_template("flaky_dashboard.html")