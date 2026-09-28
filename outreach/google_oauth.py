"""
Google OAuth 2.0 and Gmail API Sender.
Modern, passwordless authentication using official Google OAuth 2.0 with the gmail.send scope.
"""
import json
import time
import base64
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import requests

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class GoogleOAuthManager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.token_file = root_dir / "output" / "google_token.json"
        self.creds_file = root_dir / "client_secret.json"

    def get_client_credentials(self, config_outreach: Dict[str, Any]) -> Tuple[str, str]:
        """Retrieve Client ID and Client Secret from client_secret.json or config."""
        client_id = config_outreach.get("google_client_id", "").strip()
        client_secret = config_outreach.get("google_client_secret", "").strip()

        if (not client_id or not client_secret) and self.creds_file.exists():
            try:
                with open(self.creds_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    web = data.get("web") or data.get("installed") or {}
                    client_id = web.get("client_id", client_id)
                    client_secret = web.get("client_secret", client_secret)
            except Exception:
                pass

        return client_id, client_secret

    def get_authorization_url(self, client_id: str, redirect_uri: str, state: str = "google_auth") -> str:
        """Generate Google OAuth 2.0 authorization URL."""
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",  # Crucial to receive a refresh_token
            "prompt": "consent",       # Ensures refresh_token is returned on every grant
            "state": state
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Exchange authorization code for access and refresh tokens."""
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        try:
            resp = requests.post(TOKEN_URL, data=payload, timeout=15)
            data = resp.json()

            if resp.status_code != 200:
                err = data.get("error_description") or data.get("error") or "Token exchange failed"
                return False, f"Google Error: {err}", {}

            # Fetch user email for identification
            access_token = data.get("access_token")
            user_email = ""
            try:
                u_resp = requests.get(
                    USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10
                )
                if u_resp.status_code == 200:
                    user_email = u_resp.json().get("email", "")
            except Exception:
                pass

            token_data = {
                "access_token": access_token,
                "refresh_token": data.get("refresh_token", ""),
                "expires_at": time.time() + data.get("expires_in", 3600) - 60,
                "user_email": user_email,
                "client_id": client_id,
                "client_secret": client_secret
            }

            self.save_token_data(token_data)
            return True, f"Successfully authenticated as {user_email or 'Google User'}", token_data
        except Exception as e:
            return False, f"Network error during OAuth token exchange: {str(e)}", {}

    def get_valid_access_token(self) -> Optional[str]:
        """Return a valid access token, automatically refreshing if expired."""
        data = self.load_token_data()
        if not data:
            return None

        access_token = data.get("access_token")
        expires_at = data.get("expires_at", 0)
        refresh_token = data.get("refresh_token")
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")

        # If token is still fresh (has at least 30 seconds left)
        if access_token and time.time() < expires_at:
            return access_token

        # Needs refresh
        if refresh_token and client_id and client_secret:
            try:
                resp = requests.post(
                    TOKEN_URL,
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    },
                    timeout=15
                )
                if resp.status_code == 200:
                    r_data = resp.json()
                    new_access = r_data.get("access_token")
                    data["access_token"] = new_access
                    data["expires_at"] = time.time() + r_data.get("expires_in", 3600) - 60
                    if r_data.get("refresh_token"):
                        data["refresh_token"] = r_data.get("refresh_token")
                    self.save_token_data(data)
                    return new_access
            except Exception as e:
                print(f"Error refreshing Google OAuth token: {e}")

        return None

    def send_via_gmail_api(self, mime_message) -> Tuple[bool, str]:
        """Send an RFC 2822 email message using the official Gmail REST API."""
        token = self.get_valid_access_token()
        if not token:
            return False, "Google OAuth session expired or not authenticated. Please re-authenticate."

        try:
            raw_encoded = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("ascii")
            resp = requests.post(
                GMAIL_SEND_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"raw": raw_encoded},
                timeout=25
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                msg_id = data.get("id", "")
                return True, f"Sent via Gmail API (ID: {msg_id})"
            else:
                err = resp.json().get("error", {}).get("message") or resp.text
                return False, f"Gmail API error: {err}"
        except Exception as e:
            return False, f"Failed to send via Gmail API: {str(e)}"

    def get_status(self) -> Dict[str, Any]:
        """Return current authentication state."""
        data = self.load_token_data()
        if not data:
            return {"authenticated": False, "email": None}

        email = data.get("user_email")
        has_token = bool(data.get("access_token") or data.get("refresh_token"))
        return {
            "authenticated": has_token,
            "email": email or "Connected Account"
        }

    def revoke(self) -> bool:
        """Revoke token and delete local token storage."""
        data = self.load_token_data()
        token = data.get("access_token") if data else None
        if token:
            try:
                requests.post(
                    f"https://oauth2.googleapis.com/revoke?token={token}",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=5
                )
            except Exception:
                pass

        if self.token_file.exists():
            try:
                self.token_file.unlink()
            except Exception:
                pass
        return True

    def save_token_data(self, data: Dict[str, Any]):
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_token_data(self) -> Dict[str, Any]:
        if not self.token_file.exists():
            return {}
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
