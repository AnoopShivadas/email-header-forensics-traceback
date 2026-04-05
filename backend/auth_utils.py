from functools import wraps
from flask import session, redirect, url_for, request, jsonify


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # If request expects JSON (API call)
            if request.accept_mimetypes.best == "application/json" or request.is_json:
                return jsonify({"error": "Authentication required"}), 401

            # Otherwise redirect to login page
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function
