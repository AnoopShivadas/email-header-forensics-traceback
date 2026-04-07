import os
from datetime import datetime, timezone
import uuid

from flask import Blueprint, redirect, session, jsonify, url_for
from authlib.integrations.flask_client import OAuth
from backend.models import SessionLocal, User

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()


def init_oauth(app):
    """
    Initialize Google OAuth with Flask app
    """
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        },
    )


# -------------------------------------------------
# GOOGLE LOGIN (START)
# -------------------------------------------------
@auth_bp.route("/auth/google")
def google_login():
    redirect_uri = url_for("auth.auth_callback", _external=True)

    nonce = os.urandom(16).hex()
    session["nonce"] = nonce

    return oauth.google.authorize_redirect(
        redirect_uri=redirect_uri,
        nonce=nonce
    )


# -------------------------------------------------
# GOOGLE CALLBACK
# -------------------------------------------------
@auth_bp.route("/auth/callback")
def auth_callback():
    """
    Handle Google OAuth callback
    """
    try:
        token = oauth.google.authorize_access_token()

        nonce = session.pop("nonce", None)
        if not nonce:
            return jsonify({"error": "Invalid login session"}), 400

        user_info = oauth.google.parse_id_token(token, nonce=nonce)

        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")

        if not google_id or not email:
            return jsonify({"error": "User info not received"}), 400

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.google_id == google_id).first()

            if not user:
                user = User(
                    google_id=google_id,
                    email=email,
                    name=name
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # 🔐 Session values
            session["user_id"] = user.id
            session["email"] = user.email
            session["name"] = user.name

            # ✅ Added: session metadata for Settings page
            session["login_time"] = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p (UTC)")
            session["session_id"] = str(uuid.uuid4())[:8]

            return redirect("/dashboard")

        finally:
            db.close()

    except Exception as e:
        return jsonify({
            "error": "Authentication failed",
            "details": str(e)
        }), 500

# -------------------------------------------------
# MANUAL LOGIN (DEMO / NON-VALIDATED)
# -------------------------------------------------
@auth_bp.route("/auth/manual", methods=["POST"])
def manual_login():
    try:
        from flask import request

        payload = request.get_json()
        email = (payload.get("email") or "").strip()

        if not email:
            return jsonify({"error": "Email required"}), 400

        name = email.split("@")[0].replace(".", " ").title()

        db = SessionLocal()

        # ✅ FIX STARTS HERE
        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                google_id=f"manual-{email}",
                email=email,
                name=name,
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        # ✅ FIX ENDS HERE

        session["user_id"] = user.id   # 🔥 INTEGER NOW
        session["email"] = user.email
        session["name"] = user.name

        session["login_time"] = datetime.now(timezone.utc).strftime(
            "%d %b %Y, %I:%M %p (UTC)"
        )
        session["session_id"] = str(uuid.uuid4())[:8]

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------
#--------------
# LOGOUT
# -------------------------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
