"""
Google Sheets Sync Integration.
Supports both:
1. Google Apps Script Webhook (Instant, 0-credentials required)
2. Google Service Account API via gspread (Enterprise automated sync)
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import requests

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False


class GoogleSheetsSync:
    def __init__(self, config: Dict[str, Any], root_dir: Path):
        self.config = config.get("output", {}).get("google_sheets", {})
        self.root_dir = root_dir

    def sync_contacts(self, contacts: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Sync contacts to Google Sheets using either webhook or service account credentials.
        """
        if not contacts:
            return False, "No contacts provided to sync."

        webhook_url = self.config.get("webhook_url", "").strip()
        sheet_id = self.config.get("sheet_id", "").strip()
        cred_file = self.config.get("credentials_file", "google_credentials.json")

        # Method 1: Webhook (Google Apps Script WebApp)
        if webhook_url:
            return self._sync_via_webhook(webhook_url, contacts)

        # Method 2: Service Account via gspread
        if sheet_id:
            return self._sync_via_gspread(sheet_id, cred_file, contacts)

        return False, "Google Sheets is not configured. Please supply either a Webhook URL or a Google Sheet ID in Settings."

    def _sync_via_webhook(self, webhook_url: str, contacts: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Post structured contact rows to a Google Apps Script WebApp."""
        try:
            payload = {
                "action": "append_contacts",
                "contacts": contacts,
                "count": len(contacts)
            }
            resp = requests.post(webhook_url, json=payload, timeout=20)
            if resp.status_code in (200, 201, 302):
                return True, f"Successfully synced {len(contacts)} contacts to Google Sheets via Webhook!"
            else:
                return False, f"Google Webhook returned HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            return False, f"Failed to connect to Google Webhook: {str(e)}"

    def _sync_via_gspread(self, sheet_id: str, cred_file: str, contacts: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Append rows directly using Google Service Account credentials."""
        if not HAS_GSPREAD:
            return False, "gspread library is not installed."

        cred_path = self.root_dir / cred_file
        if not cred_path.exists():
            return False, f"Google Credentials file '{cred_file}' not found in project root."

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(str(cred_path), scopes=scopes)
            client = gspread.authorize(creds)
            
            # Open spreadsheet by ID or URL
            if "http" in sheet_id:
                sheet = client.open_by_url(sheet_id).sheet1
            else:
                sheet = client.open_by_key(sheet_id).sheet1

            # Prepare rows
            headers = ["Name", "Title", "Company", "LinkedIn URL", "Work Email", "Personal Email", "Email Verified", "Source", "Confidence", "Sync Date"]
            existing = sheet.get_all_values()
            if not existing:
                sheet.append_row(headers)

            import time
            now_str = time.strftime("%Y-%m-%d %H:%M")
            rows_to_append = []
            for c in contacts:
                rows_to_append.append([
                    c.get("Name", ""),
                    c.get("Title", ""),
                    c.get("Company", ""),
                    c.get("LinkedIn URL", "") or c.get("LinkedIn", ""),
                    c.get("Work Email", "") or c.get("Primary Email", "") or c.get("Email", ""),
                    c.get("Personal Email", ""),
                    str(c.get("Email Verified", "")),
                    c.get("Source", ""),
                    str(c.get("Confidence", "")),
                    now_str
                ])

            sheet.append_rows(rows_to_append)
            return True, f"Successfully appended {len(contacts)} rows to Google Sheet!"
        except Exception as e:
            return False, f"Google Sheets API error: {str(e)}"
