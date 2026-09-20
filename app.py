from flask import Flask, render_template, request, jsonify
from datetime import datetime
import re

app = Flask(__name__)

# Temporary in-memory database for hackathon demo
reports = [
    {
        "id": 1,
        "category": "Pothole / Road Damage",
        "severity": "Critical",
        "summary": "Large pothole reported near the college gate.",
        "latitude": 16.52654,
        "longitude": 80.59808,
        "status": "Reported",
        "created_at": "Today"
    },
    {
        "id": 2,
        "category": "Waste",
        "severity": "High",
        "summary": "Overflowing garbage bin reported near classroom area.",
        "latitude": 16.52710,
        "longitude": 80.59910,
        "status": "Reported",
        "created_at": "Today"
    },
    {
        "id": 3,
        "category": "Streetlight",
        "severity": "Medium",
        "summary": "Streetlight is not functioning near the road.",
        "latitude": 16.52580,
        "longitude": 80.59750,
        "status": "Reported",
        "created_at": "Today"
    }
]


def analyze_text(text):
    """
    Simple local AI-style analysis.
    Later this function can be connected to an actual LLM API.
    """

    text_lower = text.lower()

    # Category detection
    if any(word in text_lower for word in [
        "pothole", "road", "road damage", "crack", "broken road"
    ]):
        category = "Pothole / Road Damage"

    elif any(word in text_lower for word in [
        "streetlight", "street light", "lamp", "light is not working"
    ]):
        category = "Streetlight"

    elif any(word in text_lower for word in [
        "garbage", "waste", "bin", "dustbin", "trash", "overflowing"
    ]):
        category = "Waste"

    elif any(word in text_lower for word in [
        "water", "leak", "leakage", "pipe", "flood"
    ]):
        category = "Water"

    elif any(word in text_lower for word in [
        "noise", "loud", "sound", "speaker"
    ]):
        category = "Noise"

    elif any(word in text_lower for word in [
        "accident", "danger", "dangerous", "unsafe", "fire"
    ]):
        category = "Safety"

    else:
        category = "Other"

    # Severity detection
    if any(word in text_lower for word in [
        "accident", "crashed", "crash", "fire",
        "dangerous", "critical", "life threatening",
        "injury", "injured"
    ]):
        severity = "Critical"

    elif any(word in text_lower for word in [
        "huge", "large", "serious", "overflowing",
        "blocked", "danger", "unsafe"
    ]):
        severity = "High"

    elif any(word in text_lower for word in [
        "broken", "damaged", "not working", "leak"
    ]):
        severity = "Medium"

    else:
        severity = "Low"

    # Create summary
    clean_text = text.strip()

    if len(clean_text) > 140:
        summary = clean_text[:137] + "..."
    else:
        summary = clean_text

    return {
        "category": category,
        "severity": severity,
        "summary": summary
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    text = data.get("text", "").strip()

    if not text:
        return jsonify({
            "success": False,
            "message": "Please describe the problem."
        }), 400

    result = analyze_text(text)

    return jsonify({
        "success": True,
        "analysis": result
    })


@app.route("/api/reports", methods=["GET"])
def get_reports():

    return jsonify({
        "success": True,
        "reports": reports
    })


@app.route("/api/reports", methods=["POST"])
def create_report():

    data = request.get_json()

    text = data.get("text", "").strip()

    if not text:
        return jsonify({
            "success": False,
            "message": "Problem description is required."
        }), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    analysis = analyze_text(text)

    new_report = {
        "id": len(reports) + 1,
        "category": analysis["category"],
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "latitude": latitude,
        "longitude": longitude,
        "status": "Reported",
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

    reports.append(new_report)

    return jsonify({
        "success": True,
        "report": new_report,
        "analysis": analysis
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )