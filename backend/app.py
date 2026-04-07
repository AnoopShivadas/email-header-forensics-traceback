import os
import json
import logging
import csv
import io

from flask import (
    Flask,
    jsonify,
    redirect,
    request,
    session,
    Response,
    render_template
)

from backend.auth import auth_bp, init_oauth
from backend.auth_utils import login_required
from backend.models import SessionLocal, Analysis, init_db, UserSettings, User
from backend.parser import parse_email_headers
from backend.geo import lookup_multiple_ips
from backend.risk import calculate_risk_score
from dotenv import load_dotenv
from datetime import datetime, timedelta
from datetime import datetime, timezone
import uuid
from flask import session
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
from flask import render_template, session



# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def ensure_user_settings(db, user_id):
    from backend.models import UserSettings
    settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    # --------------------------------------------------------------
    # FRONTEND ROUTES
    # --------------------------------------------------------------

    @app.route("/")
    def landing():
        return render_template("index.html")

    @app.route("/login")
    def login():
        if "user_id" in session:
            return redirect("/dashboard")
        return render_template("login.html")
    
    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin_id", None)
        return redirect("/admin/login")

    @app.route("/forgot-password")
    def forgot_password():
        return render_template("forgot-password.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("analyse.html")

    @app.route("/results")
    @login_required
    def results():
        return render_template("results.html")

    @app.route("/geolocation")
    @login_required
    def geolocation():
        return render_template("geolocation.html")

    @app.route("/history-page")
    @login_required
    def history_page():
        return render_template("history.html")

    @app.route("/settings")
    @login_required
    def settings():
        return render_template("settings.html")
    
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            email = request.form.get("email")

            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()

                if user and user.role == "admin":
                    session["admin_id"] = user.id
                    return redirect("/admin/dashboard")
                else:
                    return "Access Denied: Not an admin", 403

            finally:
                db.close()

        return render_template("admin_login.html")
    
    @app.route("/admin/dashboard")
    def admin_dashboard():
        if "admin_id" not in session:
            return redirect("/admin/login")

        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.id == session["admin_id"]).first()

            if not admin or admin.role != "admin":
                return "Access Denied", 403

            users = db.query(User).all()
            analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(50).all()

            return render_template("admin_dashboard.html", users=users, analyses=analyses)

        finally:
            db.close()


    @app.route("/admin/export/pdf")
    def admin_export_pdf():

        if "admin_id" not in session:
            return redirect("/admin/login")

        db = SessionLocal()
        try:
            users = db.query(User).all()
            analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(50).all()

            buffer = io.BytesIO()

            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # TITLE
            elements.append(Paragraph("Admin Dashboard Report", styles['Title']))
            elements.append(Spacer(1, 12))

            # STATS
            elements.append(Paragraph(f"Total Users: {len(users)}", styles['Normal']))
            elements.append(Paragraph(f"Recent Analyses: {len(analyses)}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # USERS TABLE
            user_data = [["ID", "Email", "Name", "Role"]]

            for u in users:
                user_data.append([str(u.id), u.email, u.name, u.role])

            user_table = Table(user_data)
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))

            elements.append(Paragraph("Users", styles['Heading2']))
            elements.append(user_table)
            elements.append(Spacer(1, 20))

            # ANALYSIS TABLE
            analysis_data = [["ID", "User", "Risk", "Verdict"]]

            for a in analyses:
                analysis_data.append([
                    str(a.id),
                    str(a.user_id),
                    str(a.risk_score),
                    a.verdict
                ])

            analysis_table = Table(analysis_data)
            analysis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))

            elements.append(Paragraph("Recent Analyses", styles['Heading2']))
            elements.append(analysis_table)

            # BUILD PDF
            doc.build(elements)

            buffer.seek(0)

            return send_file(
                buffer,
                as_attachment=True,
                download_name="admin_dashboard_report.pdf",
                mimetype='application/pdf'
            )

        finally:
            db.close()
    # --------------------------------------------------------------
    # SESSION INITIALIZATION
    # --------------------------------------------------------------

    @app.before_request
    def ensure_session_metadata():
        if "user_id" in session:

            # Ensure login time
            if "login_time" not in session:
                session["login_time"] = datetime.now(timezone.utc).strftime(
                    "%d %b %Y, %I:%M %p (UTC)"
                )

            # Ensure session id
            if "session_id" not in session:
                session["session_id"] = str(uuid.uuid4())[:8]

            # IMPORTANT FIX:
            # If user just logged in and no active analysis is set,
            # explicitly clear any stale reference
            if "current_analysis_id" not in session:
                session["current_analysis_id"] = None

    # --------------------------------------------------------------
    # ANALYSIS API
    # --------------------------------------------------------------

    @app.route("/analyze", methods=["POST"])
    @login_required
    def analyze():
        try:
            data = request.get_json()

            if not data or "header_text" not in data:
                return jsonify({"error": "Missing header_text"}), 400

            header_text = data["header_text"].strip()

            if not header_text:
                return jsonify({"error": "Empty header_text"}), 400

            parsed = parse_email_headers(header_text)
            geo_results = lookup_multiple_ips(parsed.get("ip_addresses", []))
            risk_result = calculate_risk_score(parsed, geo_results)

            db = SessionLocal()
            settings = db.query(UserSettings).filter_by(
                user_id=session["user_id"]
            ).first()

            # =====================================================
            # AUTO-SAVE OFF → STORE TEMPORARILY IN SESSION
            # =====================================================
            if settings and not settings.auto_save:

                session["temp_analysis_data"] = {
                    "parsed": parsed,
                    "geo": geo_results,
                    "risk": risk_result
                }

                session["current_analysis_id"] = "temp"

                return jsonify({
                    "analysis_id": "temp",
                    "risk_score": risk_result["risk_score"],
                    "verdict": risk_result["verdict"],
                    "notification": bool(settings.email_notifications)
                }), 200

            # =====================================================
            # AUTO-SAVE ON → STORE IN DATABASE
            # =====================================================
            try:
                analysis = Analysis(
                    user_id=session["user_id"],
                    header_text=header_text,
                    risk_score=risk_result["risk_score"],
                    verdict=risk_result["verdict"],
                    result_json=json.dumps({
                        "parsed": parsed,
                        "geo": geo_results,
                        "risk": risk_result
                    })
                )

                db.add(analysis)
                db.commit()
                db.refresh(analysis)

                session["current_analysis_id"] = analysis.id
                session.pop("temp_analysis_data", None)

                return jsonify({
                    "analysis_id": analysis.id,
                    "risk_score": analysis.risk_score,
                    "verdict": analysis.verdict,
                    "notification": bool(settings and settings.email_notifications)
                }), 200

            finally:
                db.close()

        except Exception:
            logger.exception("Analysis failed")
            return jsonify({"error": "Analysis failed"}), 500

    # --------------------------------------------------------------
    # RESULTS API 
    # --------------------------------------------------------------

    @app.route("/api/latest-result")
    @login_required
    def latest_result():

        active_id = session.get("current_analysis_id")

        # TEMP SESSION MODE
        if active_id == "temp":
            data = session.get("temp_analysis_data")
            if not data:
                return jsonify({"empty": True}), 200

            parsed = data.get("parsed", {})
            risk = data.get("risk", {})

            geo_entries = data.get("geo", [])
            real_hops = parsed.get("received_hops", [])

            hop_count = len(geo_entries) if geo_entries else len(real_hops)
            if hop_count == 0:
                hop_count = 1

            return jsonify({
                "id": "temp",
                "risk_score": risk.get("risk_score"),
                "verdict": risk.get("verdict"),
                "summary": risk.get("summary"),
                "findings": risk.get("findings", []),
                "spf": parsed.get("spf_result"),
                "dkim": parsed.get("dkim_present"),
                "dmarc": parsed.get("dmarc_present"),
                "from": parsed.get("from_address"),
                "to": parsed.get("to_address"),
                "subject": parsed.get("subject"),
                "date": parsed.get("date"),
                "hop_count": hop_count
            })

        # NORMAL DB MODE
        if not active_id:
            return jsonify({"empty": True}), 200

        db = SessionLocal()
        try:
            analysis = db.query(Analysis).filter(
                Analysis.id == active_id,
                Analysis.user_id == session["user_id"]
            ).first()

            if not analysis:
                return jsonify({"empty": True}), 200

            data = json.loads(analysis.result_json or "{}")
            parsed = data.get("parsed", {})
            risk = data.get("risk", {})

            geo_entries = data.get("geo", [])
            real_hops = parsed.get("received_hops", [])

            hop_count = len(geo_entries) if geo_entries else len(real_hops)
            if hop_count == 0:
                hop_count = 1

            return jsonify({
                "id": analysis.id,
                "risk_score": analysis.risk_score,
                "verdict": analysis.verdict,
                "summary": risk.get("summary"),
                "findings": risk.get("findings", []),
                "spf": parsed.get("spf_result"),
                "dkim": parsed.get("dkim_present"),
                "dmarc": parsed.get("dmarc_present"),
                "from": parsed.get("from_address"),
                "to": parsed.get("to_address"),
                "subject": parsed.get("subject"),
                "date": parsed.get("date"),
                "hop_count": hop_count
            })
        finally:
            db.close()

    # --------------------------------------------------------------
    # GEOLOCATION API 
    # --------------------------------------------------------------

    @app.route("/api/geolocation/latest", methods=["GET"])
    @login_required
    def latest_geolocation():
        active_id = session.get("current_analysis_id")
        if not active_id:
            return jsonify({"hops": [], "empty": True}), 200

        if active_id == "temp":

            temp_data = session.get("temp_analysis_data")

            if not temp_data:
                # Defensive reset
                session["current_analysis_id"] = None
                return jsonify({"hops": [], "empty": True}), 200

            geo_entries = temp_data.get("geo", [])

            hops = []
            index = 1

            for g in geo_entries:
                hops.append({
                    "stage": f"Hop {index}",
                    "ip": g.get("ip") or "Unknown",
                    "city": g.get("city") or "Unknown",
                    "country": g.get("country") or "Unknown",
                    "org": g.get("organization") or "Unknown ISP",
                    "latitude": g.get("latitude"),
                    "longitude": g.get("longitude"),
                    "timestamp": None
                })
                index += 1

            # Preserve your destination logic
            if len(hops) == 1:
                hops.append({
                    "stage": "Destination",
                    "ip": "Not disclosed",
                    "city": "Unknown",
                    "country": "Unknown",
                    "org": "Destination Mail Server",
                    "latitude": None,
                    "longitude": None,
                    "timestamp": None
                })

            return jsonify({"hops": hops})

        db = SessionLocal()
        try:
            analysis = db.query(Analysis).filter(
                Analysis.id == active_id,
                Analysis.user_id == session["user_id"]
            ).first()

            if not analysis:
                session["current_analysis_id"] = None
                return jsonify({"hops": [], "empty": True}), 200

            data = json.loads(analysis.result_json or "{}")
            geo_entries = data.get("geo", [])

            hops = []
            index = 1

            for g in geo_entries:
                hops.append({
                    "stage": f"Hop {index}",
                    "ip": g.get("ip") or "Unknown",
                    "city": g.get("city") or "Unknown",
                    "country": g.get("country") or "Unknown",
                    "org": g.get("organization") or "Unknown ISP",
                    "latitude": g.get("latitude"),
                    "longitude": g.get("longitude"),
                    "timestamp": None
                })
                index += 1

            if len(hops) == 1:
                hops.append({
                    "stage": "Destination",
                    "ip": "Not disclosed",
                    "city": "Unknown",
                    "country": "Unknown",
                    "org": "Destination Mail Server",
                    "latitude": None,
                    "longitude": None,
                    "timestamp": None
                })

            return jsonify({"hops": hops})

        finally:
            db.close()

    @app.route("/api/geolocation/<int:analysis_id>", methods=["GET"])
    @login_required
    def geolocation_by_analysis(analysis_id):
        db = SessionLocal()
        try:
            analysis = (
                db.query(Analysis)
                .filter(
                    Analysis.id == analysis_id,
                    Analysis.user_id == session["user_id"]
                )
                .first()
            )

            if not analysis:
                return jsonify({"hops": []}), 404

            data = json.loads(analysis.result_json or "{}")
            geo_entries = data.get("geo", [])

            hops = []
            index = 1

            for g in geo_entries:
                hops.append({
                    "stage": f"Hop {index}",
                    "ip": g.get("ip") or "Unknown",
                    "city": g.get("city") or "Unknown",
                    "country": g.get("country") or "Unknown",
                    "org": g.get("organization") or "Unknown ISP",
                    "latitude": g.get("latitude"),
                    "longitude": g.get("longitude"),
                    "timestamp": None
                })
                index += 1

            geo_entries = data.get("geo", [])
            real_hops = data["parsed"].get("received_hops", [])

            hop_count = len(geo_entries) if geo_entries else len(real_hops)
            if hop_count == 0:
                hop_count = 1

            return jsonify({
                "risk_score": analysis.risk_score,
                "verdict": analysis.verdict,
                "summary": data["risk"].get("summary", ""),
                "findings": data["risk"].get("findings", []),
                "spf": data["parsed"].get("spf_result"),
                "dkim": data["parsed"].get("dkim_present"),
                "dmarc": data["parsed"].get("dmarc_present"),
                "from": data["parsed"].get("from_address"),
                "to": data["parsed"].get("to_address"),
                "subject": data["parsed"].get("subject"),
                "date": data["parsed"].get("date"),
                "hop_count": hop_count
            }), 200

        finally:
            db.close()


    # --------------------------------------------------------------
    # HISTORY APIs
    # --------------------------------------------------------------

    @app.route("/api/history/stats", methods=["GET"])
    @login_required
    def history_stats():
        db = SessionLocal()
        try:
            analyses = (
                db.query(Analysis)
                .filter(Analysis.user_id == session["user_id"])
                .all()
            )

            stats = {
                "total": len(analyses),
                "safe": 0,
                "suspicious": 0,
                "threat": 0
            }

            for a in analyses:
                verdict = (a.verdict or "").lower()
                if verdict == "safe":
                    stats["safe"] += 1
                elif verdict == "suspicious":
                    stats["suspicious"] += 1
                elif verdict == "threat":
                    stats["threat"] += 1

            return jsonify(stats), 200

        finally:
            db.close()

    @app.route("/api/history", methods=["GET"])
    @login_required
    def history_list():
        db = SessionLocal()
        try:
            risk = request.args.get("risk")
            days = request.args.get("days")
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("page_size", 5))

            query = db.query(Analysis).filter(
                Analysis.user_id == session["user_id"]
            )

            if risk:
                query = query.filter(Analysis.verdict.ilike(risk))

            if days and days.isdigit():
                since = datetime.utcnow() - timedelta(days=int(days))
                query = query.filter(Analysis.created_at >= since)

            total_items = query.count()
            total_pages = max((total_items + page_size - 1) // page_size, 1)

            analyses = (
                query
                .order_by(Analysis.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            items = []
            for a in analyses:
                data = json.loads(a.result_json or "{}")
                parsed = data.get("parsed", {})

                items.append({
                    "id": a.id,
                    "date": a.created_at.strftime("%Y-%m-%d"),
                    "sender": parsed.get("from_address", "—"),
                    "subject": parsed.get("subject", "—"),
                    "risk_score": a.risk_score,
                    "verdict": a.verdict
                })

            return jsonify({
                "items": items,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items
            }), 200

        finally:
            db.close()

    # --------------------------------------------------------------
    # ANALYSIS BY ID
    # --------------------------------------------------------------

    @app.route("/api/analysis/<int:analysis_id>", methods=["GET"])
    @login_required
    def analysis_by_id(analysis_id):
        db = SessionLocal()
        try:
            analysis = (
                db.query(Analysis)
                .filter(
                    Analysis.id == analysis_id,
                    Analysis.user_id == session["user_id"]
                )
                .first()
            )

            if not analysis:
                return jsonify({"error": "Analysis not found"}), 404

            data = json.loads(analysis.result_json)

            return jsonify({
                "risk_score": analysis.risk_score,
                "verdict": analysis.verdict,
                "summary": data["risk"].get("summary", ""),
                "findings": data["risk"].get("findings", []),
                "spf": data["parsed"].get("spf_result"),
                "dkim": data["parsed"].get("dkim_present"),
                "dmarc": data["parsed"].get("dmarc_present"),
                "from": data["parsed"].get("from_address"),
                "to": data["parsed"].get("to_address"),
                "subject": data["parsed"].get("subject"),
                "date": data["parsed"].get("date"),
                "hop_count": len(data["parsed"].get("received_hops", []))
            }), 200

        finally:
            db.close()

    @app.route("/api/settings", methods=["GET"])
    @login_required
    def get_settings():
        db = SessionLocal()
        try:
            ensure_user_settings(db, session["user_id"])

            settings = db.query(UserSettings).filter_by(
                user_id=session["user_id"]
            ).first()

            return jsonify({
                "auto_save": bool(settings.auto_save),
                "email_notifications": bool(settings.email_notifications),
                "export_format": settings.export_format
            })
        finally:
            db.close()

    @app.route("/api/settings", methods=["POST"])
    @login_required
    def update_settings():
        data = request.get_json()
        db = SessionLocal()
        try:
            ensure_user_settings(db, session["user_id"])

            settings = db.query(UserSettings).filter_by(
                user_id=session["user_id"]
            ).first()

            if "auto_save" in data:
                settings.auto_save = 1 if data["auto_save"] else 0

            if "email_notifications" in data:
                settings.email_notifications = 1 if data["email_notifications"] else 0

            if "export_format" in data:
                settings.export_format = data["export_format"]

            settings.updated_at = datetime.now(timezone.utc)
            db.commit()

            return jsonify({"status": "ok"})
        finally:
            db.close()

    @app.route("/api/history/clear", methods=["POST"])
    @login_required
    def clear_history():
        db = SessionLocal()
        try:
            db.query(Analysis).filter(
                Analysis.user_id == session["user_id"]
            ).delete()
            db.commit()
            return jsonify({"status": "cleared"})
        finally:
            db.close()

    # --------------------------------------------------------------
    # CSV EXPORT
    # --------------------------------------------------------------

    @app.route("/export/csv")
    @login_required
    def export_csv():
        analysis_id = request.args.get("analysis_id", type=int)
        if not analysis_id:
            return "Missing analysis_id", 400

        db = SessionLocal()
        try:
            analysis = db.query(Analysis).filter(
                Analysis.id == analysis_id,
                Analysis.user_id == session["user_id"]
            ).first()

            if not analysis:
                return "Analysis not found", 404

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Risk Score", "Verdict", "Date"])

            writer.writerow([
                analysis.risk_score,
                analysis.verdict,
                analysis.created_at.isoformat()
            ])

            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition":
                    "attachment; filename=analysis.csv"
                }
            )

        finally:
            db.close()


    @app.route("/export/history")
    @login_required
    def export_full_history():
        db = SessionLocal()
        try:
            analyses = (
                db.query(Analysis)
                .filter(Analysis.user_id == session["user_id"])
                .order_by(Analysis.created_at.desc())
                .all()
            )

            if not analyses:
                return "No history available", 404

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow([
                "Analysis ID",
                "Date",
                "From",
                "To",
                "Subject",
                "Risk Score",
                "Verdict",
                "SPF",
                "DKIM",
                "DMARC",
                "IP Hop Count"
            ])

            for a in analyses:
                data = json.loads(a.result_json or "{}")
                parsed = data.get("parsed", {})

                writer.writerow([
                    a.id,
                    a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    parsed.get("from_address", "—"),
                    parsed.get("to_address", "—"),
                    parsed.get("subject", "—"),
                    a.risk_score,
                    a.verdict,
                    parsed.get("spf_result", "—"),
                    parsed.get("dkim_present", "—"),
                    parsed.get("dmarc_present", "—"),
                    len(parsed.get("received_hops", []))
                ])

            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition":
                    "attachment; filename=email_forensics_full_history.csv"
                }
            )

        finally:
            db.close()

    @app.route("/export/history/json")
    @login_required
    def export_full_history_json():
        db = SessionLocal()
        try:
            analyses = (
                db.query(Analysis)
                .filter(Analysis.user_id == session["user_id"])
                .order_by(Analysis.created_at.desc())
                .all()
            )

            history = []

            for a in analyses:
                data = json.loads(a.result_json or "{}")
                parsed = data.get("parsed", {})
                risk = data.get("risk", {})

                history.append({
                    "analysis_id": a.id,
                    "created_at": a.created_at.isoformat(),
                    "from": parsed.get("from_address"),
                    "to": parsed.get("to_address"),
                    "subject": parsed.get("subject"),
                    "risk_score": a.risk_score,
                    "verdict": a.verdict,
                    "spf": parsed.get("spf_result"),
                    "dkim": parsed.get("dkim_present"),
                    "dmarc": parsed.get("dmarc_present"),
                    "hop_count": len(parsed.get("received_hops", [])),
                    "risk_summary": risk.get("summary"),
                    "findings": risk.get("findings", [])
                })

            return Response(
                json.dumps(history, indent=2),
                mimetype="application/json",
                headers={
                    "Content-Disposition":
                    "attachment; filename=email_forensics_full_history.json"
                }
            )

        finally:
            db.close()

    @app.route("/export/history/pdf")
    @login_required
    def export_full_history_pdf():
        db = SessionLocal()
        try:
            analyses = (
                db.query(Analysis)
                .filter(Analysis.user_id == session["user_id"])
                .order_by(Analysis.created_at.desc())
                .all()
            )

            if not analyses:
                return "No history available", 404

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # ===== TITLE =====
            elements.append(Paragraph("Email Forensics – Analysis History Report", styles['Title']))
            elements.append(Spacer(1, 10))

            # ===== DATE =====
            elements.append(Paragraph(
                f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                styles['Normal']
            ))
            elements.append(Spacer(1, 20))

            # ===== LOOP EACH ANALYSIS =====
            for a in analyses:

                data = json.loads(a.result_json or "{}")
                parsed = data.get("parsed", {})
                risk = data.get("risk", {})

                # Verdict color
                verdict_color = "#16a34a" if a.verdict == "SAFE" else "#dc2626"

                # ===== SECTION TITLE =====
                elements.append(Paragraph(f"<b>Analysis ID:</b> {a.id}", styles['Heading3']))
                elements.append(Spacer(1, 6))

                # ===== TABLE =====
                table_data = [
                    ["Field", "Value"],
                    ["Date", a.created_at.strftime('%Y-%m-%d %H:%M')],
                    ["From", Paragraph(parsed.get("from_address", "—"), styles['Normal'])],
                    ["To", parsed.get("to_address", "—")],
                    ["Subject", Paragraph(parsed.get("subject", "—"), styles['Normal'])],
                    ["Risk Score", str(a.risk_score)],
                    ["Verdict", f'<font color="{verdict_color}"><b>{a.verdict}</b></font>'],
                    ["SPF", str(parsed.get("spf_result"))],
                    ["DKIM", str(parsed.get("dkim_present"))],
                    ["DMARC", str(parsed.get("dmarc_present"))],
                ]

                table = Table(table_data, colWidths=[120, 350])

                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

                    ('BACKGROUND', (0, 1), (0, -1), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),

                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))

                elements.append(table)
                elements.append(Spacer(1, 10))

                # ===== SUMMARY =====
                summary_text = risk.get("summary", "No summary available")

                elements.append(Paragraph("<b>Summary:</b>", styles['Normal']))
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(summary_text, styles['Normal']))

                elements.append(Spacer(1, 20))

            # ===== BUILD PDF =====
            doc.build(elements)
            buffer.seek(0)

            return send_file(
                buffer,
                as_attachment=True,
                download_name="email_forensics_full_history.pdf",
                mimetype="application/pdf"
            )

        finally:
            db.close()
        # --------------------------------------------------------------
        # SINGLE ANALYSIS EXPORTS (RESULT PAGE)
        # --------------------------------------------------------------

        @app.route("/export/analysis/<int:analysis_id>/json")
        @login_required
        def export_analysis_json(analysis_id):
            db = SessionLocal()
            try:
                analysis = db.query(Analysis).filter(
                    Analysis.id == analysis_id,
                    Analysis.user_id == session["user_id"]
                ).first()

                if not analysis:
                    return "Analysis not found", 404

                data = json.loads(analysis.result_json or "{}")

                return Response(
                    json.dumps({
                        "analysis_id": analysis.id,
                        "created_at": analysis.created_at.isoformat(),
                        "risk_score": analysis.risk_score,
                        "verdict": analysis.verdict,
                        **data
                    }, indent=2),
                    mimetype="application/json",
                    headers={
                        "Content-Disposition":
                        f"attachment; filename=analysis_{analysis_id}.json"
                    }
                )
            finally:
                db.close()


    @app.route("/export/analysis/<int:analysis_id>/pdf")
    @login_required
    def export_analysis_pdf(analysis_id):
        db = SessionLocal()
        try:
            analysis = db.query(Analysis).filter(
                Analysis.id == analysis_id,
                Analysis.user_id == session["user_id"]
            ).first()

            if not analysis:
                return "Analysis not found", 404

            data = json.loads(analysis.result_json or "{}")
            parsed = data.get("parsed", {})
            risk = data.get("risk", {})

            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            y = height - 40
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(40, y, f"Email Forensics – Analysis #{analysis.id}")

            y -= 30
            pdf.setFont("Helvetica", 10)

            lines = [
                f"Date: {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"From: {parsed.get('from_address', '—')}",
                f"To: {parsed.get('to_address', '—')}",
                f"Subject: {parsed.get('subject', '—')}",
                f"Risk Score: {analysis.risk_score}",
                f"Verdict: {analysis.verdict}",
                f"SPF: {parsed.get('spf_result')}",
                f"DKIM: {parsed.get('dkim_present')}",
                f"DMARC: {parsed.get('dmarc_present')}",
                "",
                "Summary:",
                risk.get("summary", "—"),
            ]

            for line in lines:
                if y < 60:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 10)
                    y = height - 40

                pdf.drawString(40, y, line)
                y -= 14

            pdf.save()
            buffer.seek(0)

            return Response(
                buffer,
                mimetype="application/pdf",
                headers={
                    "Content-Disposition":
                    f"attachment; filename=analysis_{analysis_id}.pdf"
                }
            )
        finally:
            db.close()

    @app.route("/export/analysis/<int:analysis_id>/csv")
    @login_required
    def export_analysis_csv(analysis_id):
        db = SessionLocal()
        try:
            analysis = db.query(Analysis).filter(
                Analysis.id == analysis_id,
                Analysis.user_id == session["user_id"]
            ).first()

            if not analysis:
                return "Analysis not found", 404

            data = json.loads(analysis.result_json or "{}")
            parsed = data.get("parsed", {})
            risk = data.get("risk", {})

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(["Field", "Value"])
            writer.writerow(["Analysis ID", analysis.id])
            writer.writerow(["Date", analysis.created_at.isoformat()])
            writer.writerow(["From", parsed.get("from_address", "—")])
            writer.writerow(["To", parsed.get("to_address", "—")])
            writer.writerow(["Subject", parsed.get("subject", "—")])
            writer.writerow(["Risk Score", analysis.risk_score])
            writer.writerow(["Verdict", analysis.verdict])
            writer.writerow(["SPF", parsed.get("spf_result")])
            writer.writerow(["DKIM", parsed.get("dkim_present")])
            writer.writerow(["DMARC", parsed.get("dmarc_present")])
            writer.writerow(["Hop Count", len(parsed.get("received_hops", []))])
            writer.writerow([])
            writer.writerow(["Summary", risk.get("summary", "")])

            output.seek(0)

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition":
                    f"attachment; filename=analysis_{analysis_id}.csv"
                }
            )
        finally:
            db.close()


    return app
# ------------------------------------------------------------------
# RUN
# ------------------------------------------------------------------

app = create_app()
init_oauth(app)
app.register_blueprint(auth_bp)
init_db()

if __name__ == "__main__":
    app.run(debug=True)
