"""
Flask Web Dashboard — REST API + WebSocket server for the HR Email Finder UI.
Provides real-time pipeline progress, cold email outreach, Google OAuth 2.0, and Google Sheets sync.

Run: python dashboard/app.py
Then open: http://127.0.0.1:5000
"""
import sys
import os
import json
import time
import random
import threading
from pathlib import Path

# Ensure project root is on the path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from utils.config_loader import load_config, save_config, get_active_roles, get_enabled_tools
from scheduler import Scheduler
from outreach.templates import render_template, DEFAULT_TEMPLATES
from outreach.sender import OutreachSender
from outreach.outbox import get_outbox
from outreach.google_oauth import GoogleOAuthManager
from integrations.google_sheets import GoogleSheetsSync

app = Flask(__name__, template_folder="templates", static_folder="templates")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

scheduler = Scheduler(str(ROOT / "config.yaml"))
_pipeline_thread: threading.Thread | None = None
_pipeline_status: dict = {"running": False, "progress": 0, "total": 0, "contacts": [], "log": []}


def _load_existing_results() -> list[dict]:
    """Load all contacts from the most recent CSV in output/."""
    import csv as _csv
    out_dir = ROOT / "output"
    if not out_dir.exists():
        return []
    csvs = sorted(
        [f for f in out_dir.iterdir() if f.suffix == ".csv" and f.stat().st_size > 0],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    all_contacts = []
    seen = set()
    for csv_file in csvs:
        try:
            with open(csv_file, "r", encoding="utf-8") as fh:
                reader = _csv.DictReader(fh)
                for row in reader:
                    if "LinkedIn" in row and "LinkedIn URL" not in row:
                        row["LinkedIn URL"] = row.pop("LinkedIn", "")
                    if "Email" in row and "Primary Email" not in row:
                        row["Primary Email"] = row.get("Email", "")
                        row["Work Email"] = row.get("Email", "") if row.get("Email Type", "") not in ("personal",) else ""
                        row["Personal Email"] = ""
                    name = row.get("Name", "")
                    source = row.get("Source", "")
                    if name in ("HR Team", "Recruiting Team", "Careers Team", "People Team", "Talent Team") and source == "domain_mx":
                        continue
                    key = (name.strip().lower(), row.get("Primary Email", "").strip().lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    all_contacts.append(dict(row))
        except Exception:
            pass
    return all_contacts


_pipeline_status["contacts"] = _load_existing_results()


# ---------------------------------------------------------------------------
# Static / UI
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


# ---------------------------------------------------------------------------
# Config API
# ---------------------------------------------------------------------------

@app.route("/api/config", methods=["GET"])
def get_config():
    try:
        config = load_config(ROOT / "config.yaml")
        return jsonify({"success": True, "config": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config", methods=["POST"])
def update_config():
    try:
        data = request.get_json()
        current = load_config(ROOT / "config.yaml")
        _deep_merge(current, data)
        save_config(current, ROOT / "config.yaml")
        return jsonify({"success": True, "message": "Config saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config/tool/<tool_name>", methods=["POST"])
def toggle_tool(tool_name: str):
    """Enable or disable a specific tool."""
    try:
        data = request.get_json()
        config = load_config(ROOT / "config.yaml")
        if tool_name not in config.get("tools", {}):
            return jsonify({"success": False, "error": f"Unknown tool: {tool_name}"}), 404
        config["tools"][tool_name].update(data)
        save_config(config, ROOT / "config.yaml")
        return jsonify({"success": True, "tool": tool_name, "config": config["tools"][tool_name]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config/roles", methods=["POST"])
def update_roles():
    """Update active role presets and custom roles."""
    try:
        data = request.get_json()
        config = load_config(ROOT / "config.yaml")
        if "active_presets" in data:
            config["search"]["active_presets"] = data["active_presets"]
        if "custom" in data:
            config["search"]["role_presets"]["custom"] = data["custom"]
        save_config(config, ROOT / "config.yaml")
        return jsonify({"success": True, "roles": get_active_roles(config)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Pipeline API
# ---------------------------------------------------------------------------

@app.route("/api/run", methods=["POST"])
def run_pipeline():
    """Start a pipeline run (async, progress via WebSocket)."""
    global _pipeline_thread, _pipeline_status

    if _pipeline_status.get("running"):
        return jsonify({"success": False, "error": "Pipeline already running"}), 409

    data = request.get_json() or {}
    companies_raw = data.get("companies", [])
    csv_path = data.get("csv_path", "")

    if isinstance(companies_raw, list):
        companies = []
        for item in companies_raw:
            if isinstance(item, str):
                companies.append({"company_name": item.strip(), "website": ""})
            elif isinstance(item, dict):
                companies.append(item)
    else:
        companies = []

    if not companies and not csv_path:
        return jsonify({"success": False, "error": "Provide companies list or csv_path"}), 400

    _pipeline_status = {"running": True, "progress": 0, "total": 0, "contacts": [], "log": []}

    def run():
        global _pipeline_status
        try:
            from pipeline import Pipeline
            config = load_config(ROOT / "config.yaml")
            pipe = Pipeline(config)

            def on_event(event: str, event_data: dict):
                global _pipeline_status
                _pipeline_status.update(event_data)
                socketio.emit("pipeline_event", {"event": event, "data": event_data})

            pipe.set_progress_callback(on_event)

            if csv_path:
                contacts = pipe.run_from_csv(str(ROOT / csv_path))
            else:
                contacts = pipe.run(companies)

            _pipeline_status["contacts"] = [c.to_dict() for c in contacts]
            _pipeline_status["running"] = False
            socketio.emit("pipeline_event", {
                "event": "done",
                "data": {"contacts": _pipeline_status["contacts"]}
            })
        except Exception as ex:
            _pipeline_status["running"] = False
            socketio.emit("pipeline_event", {"event": "error", "data": {"message": str(ex)}})

    _pipeline_thread = threading.Thread(target=run, daemon=True, name="pipeline")
    _pipeline_thread.start()
    return jsonify({"success": True, "message": "Pipeline started"})


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({"success": True, "status": _pipeline_status})


@app.route("/api/results", methods=["GET"])
def get_results():
    """Return latest pipeline contacts."""
    return jsonify({
        "success": True,
        "count": len(_pipeline_status.get("contacts", [])),
        "contacts": _pipeline_status.get("contacts", []),
    })


# ---------------------------------------------------------------------------
# Scheduler API
# ---------------------------------------------------------------------------

@app.route("/api/schedule/start", methods=["POST"])
def start_schedule():
    scheduler.start()
    return jsonify({"success": True, "message": "Scheduler started"})


@app.route("/api/schedule/stop", methods=["POST"])
def stop_schedule():
    scheduler.stop()
    return jsonify({"success": True, "message": "Scheduler stopped"})


@app.route("/api/schedule/run-now", methods=["POST"])
def run_now():
    threading.Thread(target=scheduler.run_now, daemon=True).start()
    return jsonify({"success": True, "message": "Immediate run triggered"})


# ---------------------------------------------------------------------------
# Files API
# ---------------------------------------------------------------------------

@app.route("/api/files/output", methods=["GET"])
def list_output_files():
    out_dir = ROOT / "output"
    if not out_dir.exists():
        return jsonify({"success": True, "files": []})
    files = [
        {
            "name": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
        }
        for f in sorted(out_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        if f.is_file()
    ]
    return jsonify({"success": True, "files": files})


@app.route("/api/files/input-sample", methods=["GET"])
def get_input_sample():
    sample = ROOT / "input" / "companies_sample.csv"
    if sample.exists():
        return sample.read_text(encoding="utf-8"), 200, {"Content-Type": "text/plain"}
    return "", 404


# ---------------------------------------------------------------------------
# Google OAuth 2.0 API
# ---------------------------------------------------------------------------

@app.route("/api/auth/google/status", methods=["GET"])
def get_google_auth_status():
    try:
        mgr = GoogleOAuthManager(ROOT)
        st = mgr.get_status()
        config = load_config(ROOT / "config.yaml")
        outreach_cfg = config.get("outreach", {})
        c_id, _ = mgr.get_client_credentials(outreach_cfg)
        return jsonify({
            "success": True,
            "has_credentials": bool(c_id),
            "client_id": c_id,
            "auth_type": outreach_cfg.get("auth_type", "auto"),
            **st
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/google/login-url", methods=["POST"])
def get_google_login_url():
    try:
        data = request.get_json() or {}
        config = load_config(ROOT / "config.yaml")
        outreach_cfg = config.get("outreach", {})

        c_id = data.get("client_id", "").strip() or outreach_cfg.get("google_client_id", "")
        c_secret = data.get("client_secret", "").strip() or outreach_cfg.get("google_client_secret", "")

        mgr = GoogleOAuthManager(ROOT)
        if not c_id or not c_secret:
            c_id, c_secret = mgr.get_client_credentials(outreach_cfg)

        if not c_id:
            return jsonify({
                "success": False,
                "error": "Google Client ID required. Please enter Client ID & Secret or upload client_secret.json."
            }), 400

        if data.get("client_id") or data.get("client_secret"):
            outreach_cfg["google_client_id"] = c_id
            if c_secret:
                outreach_cfg["google_client_secret"] = c_secret
            config["outreach"] = outreach_cfg
            save_config(config, ROOT / "config.yaml")

        redirect_uri = request.host_url.rstrip("/") + "/api/auth/google/callback"
        auth_url = mgr.get_authorization_url(c_id, redirect_uri)
        return jsonify({"success": True, "auth_url": auth_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/google/callback", methods=["GET"])
def google_auth_callback():
    code = request.args.get("code")
    err = request.args.get("error")

    if err:
        return f"<h3>Authentication cancelled or denied: {err}</h3><p><a href='/#outreach'>Return to dashboard</a></p>", 400

    if not code:
        return "<h3>Missing authorization code</h3><p><a href='/#outreach'>Return to dashboard</a></p>", 400

    try:
        config = load_config(ROOT / "config.yaml")
        outreach_cfg = config.get("outreach", {})
        mgr = GoogleOAuthManager(ROOT)

        c_id, c_secret = mgr.get_client_credentials(outreach_cfg)
        redirect_uri = request.base_url

        ok, msg, token_data = mgr.exchange_code_for_token(code, c_id, c_secret, redirect_uri)
        if ok:
            outreach_cfg["auth_type"] = "oauth"
            if token_data.get("user_email"):
                outreach_cfg["smtp_user"] = token_data["user_email"]
            config["outreach"] = outreach_cfg
            save_config(config, ROOT / "config.yaml")

            return f"""
            <html>
            <head><title>Google OAuth Success</title></head>
            <body style="background:#09090b; color:#fff; font-family:sans-serif; text-align:center; padding-top:60px">
              <h2>Connected to Google Account Successfully!</h2>
              <p style="color:#a1a1aa">Authenticated as: <strong>{token_data.get('user_email', '')}</strong></p>
              <p>Redirecting to dashboard...</p>
              <script>
                setTimeout(function() {{
                  window.location.href = '/#outreach';
                }}, 1500);
              </script>
            </body>
            </html>
            """
        else:
            return f"<h3>OAuth Error: {msg}</h3><p><a href='/#outreach'>Return to dashboard</a></p>", 400
    except Exception as e:
        return f"<h3>Authentication exception: {str(e)}</h3><p><a href='/#outreach'>Return to dashboard</a></p>", 500


@app.route("/api/auth/google/revoke", methods=["POST"])
def revoke_google_auth():
    try:
        mgr = GoogleOAuthManager(ROOT)
        mgr.revoke()
        config = load_config(ROOT / "config.yaml")
        if "outreach" in config:
            config["outreach"]["auth_type"] = "smtp"
            save_config(config, ROOT / "config.yaml")
        return jsonify({"success": True, "message": "Google Account disconnected"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/google/upload-credentials", methods=["POST"])
def upload_google_credentials():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        f = request.files["file"]
        if not f.filename:
            return jsonify({"success": False, "error": "Empty filename"}), 400

        content = f.read().decode("utf-8")
        data = json.loads(content)
        web = data.get("web") or data.get("installed") or {}
        c_id = web.get("client_id", "")
        c_secret = web.get("client_secret", "")

        if not c_id:
            return jsonify({"success": False, "error": "Invalid client_secret.json format"}), 400

        with open(ROOT / "client_secret.json", "w", encoding="utf-8") as out_f:
            out_f.write(content)

        config = load_config(ROOT / "config.yaml")
        outreach_cfg = config.setdefault("outreach", {})
        outreach_cfg["google_client_id"] = c_id
        outreach_cfg["google_client_secret"] = c_secret
        save_config(config, ROOT / "config.yaml")

        return jsonify({
            "success": True,
            "message": "Credentials loaded successfully",
            "client_id": c_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Outreach API
# ---------------------------------------------------------------------------

@app.route("/api/outreach/config", methods=["GET"])
def get_outreach_config():
    try:
        config = load_config(ROOT / "config.yaml")
        resume_p = ROOT / config.get("outreach", {}).get("resume_path", "uploads/resume.pdf")
        mgr = GoogleOAuthManager(ROOT)
        oauth_status = mgr.get_status()

        return jsonify({
            "success": True,
            "profile": config.get("profile", {}),
            "outreach": config.get("outreach", {}),
            "oauth_status": oauth_status,
            "resume_exists": resume_p.exists() and resume_p.is_file(),
            "resume_filename": resume_p.name if resume_p.exists() else None
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/config", methods=["POST"])
def update_outreach_config():
    try:
        data = request.get_json() or {}
        config = load_config(ROOT / "config.yaml")
        if "profile" in data:
            _deep_merge(config.setdefault("profile", {}), data["profile"])
        if "outreach" in data:
            _deep_merge(config.setdefault("outreach", {}), data["outreach"])
        save_config(config, ROOT / "config.yaml")
        return jsonify({"success": True, "message": "Outreach settings saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/test-smtp", methods=["POST"])
def test_smtp():
    try:
        data = request.get_json() or {}
        config = load_config(ROOT / "config.yaml")
        if "outreach" in data:
            _deep_merge(config.setdefault("outreach", {}), data["outreach"])
        sender = OutreachSender(config, ROOT)
        ok, msg = sender.test_connection()
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/outreach/templates", methods=["GET"])
def get_templates():
    try:
        config = load_config(ROOT / "config.yaml")
        templates = config.get("outreach", {}).get("templates", []) or DEFAULT_TEMPLATES
        return jsonify({"success": True, "templates": templates})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/templates", methods=["POST"])
def save_templates():
    try:
        data = request.get_json() or {}
        templates = data.get("templates", [])
        config = load_config(ROOT / "config.yaml")
        config.setdefault("outreach", {})["templates"] = templates
        save_config(config, ROOT / "config.yaml")
        return jsonify({"success": True, "message": "Templates saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/preview", methods=["POST"])
def preview_outreach():
    try:
        data = request.get_json() or {}
        contact = data.get("contact", {})
        template_id = data.get("template_id", "")
        config = load_config(ROOT / "config.yaml")
        templates = config.get("outreach", {}).get("templates", []) or DEFAULT_TEMPLATES
        profile = config.get("profile", {})

        tpl = next((t for t in templates if t.get("id") == template_id), None)
        if not tpl and templates:
            tpl = templates[0]
        if not tpl:
            return jsonify({"success": False, "error": "Template not found"}), 404

        subject = render_template(tpl.get("subject", ""), contact, profile)
        body = render_template(tpl.get("body", ""), contact, profile)
        return jsonify({"success": True, "subject": subject, "body": body})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/send", methods=["POST"])
def send_outreach():
    try:
        data = request.get_json() or {}
        contacts = data.get("contacts", [])
        template_id = data.get("template_id", "")
        attach_resume = data.get("attach_resume", True)

        if not contacts:
            return jsonify({"success": False, "error": "No contacts selected for outreach"}), 400

        config = load_config(ROOT / "config.yaml")
        templates = config.get("outreach", {}).get("templates", []) or DEFAULT_TEMPLATES
        sender = OutreachSender(config, ROOT)

        def run_outreach():
            total = len(contacts)
            sent_count = 0
            fail_count = 0
            min_delay = float(config.get("outreach", {}).get("delay_seconds_min", 30))
            max_delay = float(config.get("outreach", {}).get("delay_seconds_max", 60))

            socketio.emit("outreach_event", {
                "event": "start",
                "data": {"total": total, "current": 0}
            })

            for idx, c in enumerate(contacts):
                ok, msg = sender.send_single_email(c, template_id, templates, attach_resume=attach_resume)
                if ok:
                    sent_count += 1
                else:
                    fail_count += 1

                socketio.emit("outreach_event", {
                    "event": "progress",
                    "data": {
                        "total": total,
                        "current": idx + 1,
                        "contact": c.get("Name", "Contact"),
                        "email": c.get("Work Email") or c.get("Primary Email"),
                        "success": ok,
                        "message": msg
                    }
                })

                if idx < total - 1:
                    delay = random.uniform(min_delay, max_delay)
                    time.sleep(delay)

            socketio.emit("outreach_event", {
                "event": "done",
                "data": {"total": total, "sent": sent_count, "failed": fail_count}
            })

        threading.Thread(target=run_outreach, daemon=True).start()
        return jsonify({"success": True, "message": f"Queued {len(contacts)} outreach email(s)"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/outbox", methods=["GET"])
def get_outbox_history():
    try:
        messages = get_outbox()
        return jsonify({"success": True, "outbox": messages, "count": len(messages)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/outreach/upload-resume", methods=["POST"])
def upload_resume():
    try:
        if "resume" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        file = request.files["resume"]
        if not file.filename:
            return jsonify({"success": False, "error": "Empty filename"}), 400

        upload_dir = ROOT / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / "resume.pdf"
        file.save(str(dest))

        config = load_config(ROOT / "config.yaml")
        config.setdefault("outreach", {})["resume_path"] = "uploads/resume.pdf"
        save_config(config, ROOT / "config.yaml")

        return jsonify({
            "success": True,
            "message": "Resume uploaded successfully",
            "filename": file.filename,
            "size": dest.stat().st_size
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Google Sheets Sync API
# ---------------------------------------------------------------------------

@app.route("/api/sync/google-sheets", methods=["POST"])
def sync_google_sheets():
    try:
        data = request.get_json() or {}
        contacts = data.get("contacts", [])

        if not contacts:
            contacts = _pipeline_status.get("contacts", [])
        if not contacts:
            contacts = _load_existing_results()

        if not contacts:
            return jsonify({"success": False, "error": "No contacts available to sync"}), 400

        config = load_config(ROOT / "config.yaml")
        sync = GoogleSheetsSync(config, ROOT)
        ok, msg = sync.sync_contacts(contacts)
        return jsonify({"success": ok, "message": msg, "count": len(contacts)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/sync/google-sheets/config", methods=["POST"])
def update_sheets_config():
    try:
        data = request.get_json() or {}
        config = load_config(ROOT / "config.yaml")
        _deep_merge(config.setdefault("output", {}).setdefault("google_sheets", {}), data)
        save_config(config, ROOT / "config.yaml")
        return jsonify({"success": True, "message": "Google Sheets settings saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep_merge(base: dict, updates: dict) -> None:
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ---------------------------------------------------------------------------
# WebSocket events
# ---------------------------------------------------------------------------

@socketio.on("connect")
def on_connect():
    emit("connected", {"status": "ok"})


if __name__ == "__main__":
    print("\n[TalentScout Server]")
    print("   Bound securely to: http://127.0.0.1:5000\n")
    # Bind to 127.0.0.1 for local security hardening
    socketio.run(app, host="127.0.0.1", port=5000, debug=False, allow_unsafe_werkzeug=True)
