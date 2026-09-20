import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request, session

BASE_DIR = Path(__file__).resolve().parent
VALID_STATUSES = {"Reported", "In Progress", "Resolved"}
app = Flask(__name__, instance_relative_config=True)
app.config.update(
    DATABASE=os.environ.get("CIVICVOICE_DATABASE", str(BASE_DIR / "instance" / "civicvoice.db")),
    SECRET_KEY=os.environ.get("CIVICVOICE_SECRET_KEY", "change-this-before-production"),
    AUTH_DEMO_MODE=os.environ.get("CIVICVOICE_AUTH_DEMO_MODE", "true").lower() == "true",
    ADMIN_IDENTIFIERS={item.strip().lower() for item in os.environ.get("CIVICVOICE_ADMIN_IDENTIFIERS", "admin@civicvoice.local").split(",") if item.strip()},
)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)

def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None: db.close()

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, identifier TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'citizen', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, description TEXT NOT NULL, summary TEXT NOT NULL, category TEXT NOT NULL, severity TEXT NOT NULL, location_text TEXT NOT NULL DEFAULT 'Location not provided', latitude REAL, longitude REAL, status TEXT NOT NULL DEFAULT 'Reported', created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id));
        CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
        CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
    """)
    db.commit()

def analyze_text(text):
    """The original local AI-style keyword classifier, retained and expanded into the new flow."""
    lowered = text.lower()
    groups = [("Pothole / Road Damage", ["pothole", "road", "road damage", "crack", "broken road"]), ("Streetlight", ["streetlight", "street light", "lamp", "light is not working"]), ("Waste", ["garbage", "waste", "bin", "dustbin", "trash", "overflowing"]), ("Water", ["water", "leak", "leakage", "pipe", "flood"]), ("Noise", ["noise", "loud", "sound", "speaker"]), ("Safety", ["accident", "danger", "dangerous", "unsafe", "fire"])]
    category = next((name for name, words in groups if any(word in lowered for word in words)), "Other")
    if any(word in lowered for word in ["accident", "crashed", "crash", "fire", "dangerous", "critical", "life threatening", "injury", "injured"]): severity = "Critical"
    elif any(word in lowered for word in ["huge", "large", "serious", "overflowing", "blocked", "danger", "unsafe"]): severity = "High"
    elif any(word in lowered for word in ["broken", "damaged", "not working", "leak"]): severity = "Medium"
    else: severity = "Low"
    clean = text.strip()
    return {"category": category, "severity": severity, "summary": clean[:137] + "..." if len(clean) > 140 else clean}

def current_user():
    user_id = session.get("user_id")
    return get_db().execute("SELECT id, identifier, display_name, role FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None

def user_payload(user): return {"id": user["id"], "identifier": user["identifier"], "display_name": user["display_name"], "role": user["role"]}
def require_user():
    user = current_user()
    return (user, None) if user else (None, (jsonify(success=False, message="Please sign in before submitting a report."), 401))
def report_payload(row):
    result = dict(row)
    result["reporter_name"] = result.pop("display_name", None) or "Community member"
    return result

@app.route("/")
def home(): return render_template("index.html")
@app.route("/health")
def health(): return jsonify(success=True, service="CivicVoice")

@app.route("/api/auth/request-code", methods=["POST"])
def request_code():
    identifier = (request.get_json(silent=True) or {}).get("identifier", "").strip().lower()
    email = re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", identifier)
    phone = re.fullmatch(r"\+?[0-9][0-9\s-]{7,18}", identifier)
    if not (email or phone): return jsonify(success=False, message="Enter a valid email address or phone number."), 400
    if not app.config["AUTH_DEMO_MODE"]: return jsonify(success=False, message="Authentication delivery is not configured. See the deployment guide."), 503
    session["pending_identifier"] = identifier
    return jsonify(success=True, message="Development verification code created.", dev_code="123456")

@app.route("/api/auth/verify", methods=["POST"])
def verify_code():
    data = request.get_json(silent=True) or {}
    identifier, code = data.get("identifier", "").strip().lower(), data.get("code", "").strip()
    if identifier != session.get("pending_identifier") or code != "123456" or not app.config["AUTH_DEMO_MODE"]: return jsonify(success=False, message="The verification code is invalid or expired."), 400
    db = get_db(); user = db.execute("SELECT id, identifier, display_name, role FROM users WHERE identifier = ?", (identifier,)).fetchone()
    if user is None:
        name = identifier.split("@")[0].replace(".", " ").replace("_", " ").title() if "@" in identifier else "Community member"
        role = "admin" if identifier in app.config["ADMIN_IDENTIFIERS"] else "citizen"
        cursor = db.execute("INSERT INTO users (identifier, display_name, role, created_at) VALUES (?, ?, ?, ?)", (identifier, name, role, utc_now())); db.commit()
        user = db.execute("SELECT id, identifier, display_name, role FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    session.clear(); session["user_id"] = user["id"]
    return jsonify(success=True, user=user_payload(user))

@app.route("/api/auth/me")
def me():
    user = current_user(); return jsonify(success=True, user=user_payload(user) if user else None)
@app.route("/api/auth/logout", methods=["POST"])
def logout(): session.clear(); return jsonify(success=True)
@app.route("/api/analyze", methods=["POST"])
def analyze():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    return jsonify(success=True, analysis=analyze_text(text)) if text else (jsonify(success=False, message="Please describe the problem."), 400)

@app.route("/api/reports", methods=["GET"])
def get_reports():
    user, mine = current_user(), request.args.get("mine") == "1"
    if mine and user is None: return jsonify(success=False, message="Please sign in to view your complaints."), 401
    query = "SELECT reports.*, users.display_name FROM reports LEFT JOIN users ON reports.user_id = users.id"; params = ()
    if mine: query += " WHERE reports.user_id = ?"; params = (user["id"],)
    rows = get_db().execute(query + " ORDER BY reports.created_at DESC", params).fetchall()
    return jsonify(success=True, reports=[report_payload(row) for row in rows])

@app.route("/api/reports", methods=["POST"])
def create_report():
    user, error = require_user()
    if error: return error
    data = request.get_json(silent=True) or {}; text = data.get("text", "").strip()
    if not text: return jsonify(success=False, message="Problem description is required."), 400
    try: latitude = float(data["latitude"]) if data.get("latitude") is not None else None; longitude = float(data["longitude"]) if data.get("longitude") is not None else None
    except (TypeError, ValueError): return jsonify(success=False, message="Location coordinates are invalid."), 400
    if (latitude is not None and not -90 <= latitude <= 90) or (longitude is not None and not -180 <= longitude <= 180): return jsonify(success=False, message="Location coordinates are outside their valid range."), 400
    analysis, now = analyze_text(text), utc_now(); location = data.get("location_text", "").strip() or "Location not provided"; db = get_db()
    cursor = db.execute("INSERT INTO reports (user_id,description,summary,category,severity,location_text,latitude,longitude,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?, 'Reported',?,?)", (user["id"], text, analysis["summary"], analysis["category"], analysis["severity"], location, latitude, longitude, now, now)); db.commit()
    row = db.execute("SELECT reports.*, users.display_name FROM reports JOIN users ON reports.user_id = users.id WHERE reports.id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(success=True, report=report_payload(row), analysis=analysis), 201

def admin_only():
    user, error = require_user()
    if error: return None, error
    if user["role"] != "admin": return None, (jsonify(success=False, message="Administrator access is required."), 403)
    return user, None
@app.route("/api/admin/reports")
def admin_reports():
    _user, error = admin_only()
    if error: return error
    rows = get_db().execute("SELECT reports.*, users.display_name FROM reports LEFT JOIN users ON reports.user_id = users.id ORDER BY reports.created_at DESC").fetchall()
    return jsonify(success=True, reports=[report_payload(row) for row in rows])
@app.route("/api/admin/reports/<int:report_id>/status", methods=["PATCH"])
def update_status(report_id):
    _user, error = admin_only()
    if error: return error
    status = (request.get_json(silent=True) or {}).get("status", "")
    if status not in VALID_STATUSES: return jsonify(success=False, message="Status must be Reported, In Progress, or Resolved."), 400
    db = get_db(); cursor = db.execute("UPDATE reports SET status=?, updated_at=? WHERE id=?", (status, utc_now(), report_id))
    if cursor.rowcount == 0: return jsonify(success=False, message="Complaint not found."), 404
    db.commit(); return jsonify(success=True, status=status)
@app.route("/api/stats")
def stats():
    counts = {status: 0 for status in VALID_STATUSES}; counts.update({row["status"]: row["count"] for row in get_db().execute("SELECT status, COUNT(*) count FROM reports GROUP BY status")})
    return jsonify(success=True, total=sum(counts.values()), by_status=counts)

with app.app_context(): init_db()
if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
