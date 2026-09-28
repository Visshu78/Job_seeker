"""
Outbox and Delivery Tracking Store.
Records every outreach attempt with timestamp, recipient, subject, and status.
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

OUTBOX_FILE = Path("output") / "outbox.json"


def get_outbox() -> List[Dict[str, Any]]:
    """Return all recorded outbox messages, newest first."""
    if not OUTBOX_FILE.exists():
        return []
    try:
        with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return sorted(data, key=lambda x: x.get("timestamp", 0), reverse=True)
    except Exception:
        return []


def record_outbox_entry(
    recipient_email: str,
    recipient_name: str,
    company: str,
    subject: str,
    status: str,  # 'SENT', 'FAILED'
    error_message: Optional[str] = None,
    template_id: Optional[str] = None
) -> Dict[str, Any]:
    """Append a new send event to the outbox."""
    OUTBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if OUTBOX_FILE.exists():
        try:
            with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            entries = []

    entry = {
        "id": f"msg_{int(time.time() * 1000)}",
        "timestamp": time.time(),
        "date_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
        "company": company,
        "subject": subject,
        "status": status,
        "error": error_message,
        "template_id": template_id,
    }
    entries.append(entry)

    try:
        with open(OUTBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving outbox entry: {e}")

    return entry
