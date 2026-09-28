"""
Outreach Sender Engine.
Supports both:
1. Google OAuth 2.0 (Modern security standard — passwordless token via Gmail REST API)
2. Traditional SMTP with TLS/SSL (Fallback for custom mail servers or App Passwords)
"""
import smtplib
import ssl
import time
import random
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from outreach.templates import render_template
from outreach.outbox import record_outbox_entry
from outreach.google_oauth import GoogleOAuthManager


class OutreachSender:
    def __init__(self, config: Dict[str, Any], root_dir: Path):
        self.config = config.get("outreach", {})
        self.profile = config.get("profile", {})
        self.root_dir = root_dir
        self.oauth_mgr = GoogleOAuthManager(root_dir)

    def is_oauth_active(self) -> bool:
        """Check if Google OAuth is configured and actively authenticated."""
        auth_type = self.config.get("auth_type", "auto")
        if auth_type == "smtp":
            return False
        status = self.oauth_mgr.get_status()
        return status.get("authenticated", False)

    def test_connection(self) -> Tuple[bool, str]:
        """Test authentication (either Google OAuth or SMTP)."""
        if self.is_oauth_active():
            token = self.oauth_mgr.get_valid_access_token()
            if token:
                st = self.oauth_mgr.get_status()
                return True, f"Google OAuth 2.0 verified: Connected as {st.get('email', 'Google Account')}"
            else:
                return False, "Google OAuth session expired. Please click 'Connect Google Account' to re-authenticate."

        # Traditional SMTP fallback
        host = self.config.get("smtp_host", "").strip()
        port = int(self.config.get("smtp_port", 587))
        user = self.config.get("smtp_user", "").strip()
        password = self.config.get("smtp_password", "").strip()
        use_ssl = self.config.get("use_ssl", False)

        if not host or not user or not password:
            return False, "SMTP Host, Username/Email, and App Password are required (or connect with Google OAuth)."

        try:
            if use_ssl or port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context, timeout=12) as server:
                    server.login(user, password)
            else:
                with smtplib.SMTP(host, port, timeout=12) as server:
                    server.ehlo()
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(user, password)
            return True, f"Connected and authenticated successfully via SMTP as {user}"
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed: Check email and App Password. (Tip: for Gmail, generate an App Password in Google Account settings or use Google OAuth)."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def send_single_email(
        self,
        contact: Dict[str, Any],
        template_id: str,
        templates: List[Dict[str, Any]],
        attach_resume: bool = True
    ) -> Tuple[bool, str]:
        """Send outreach email using either Google OAuth Gmail API or SMTP."""
        to_email = contact.get("Work Email") or contact.get("Primary Email") or contact.get("Email")
        if not to_email or "@" not in to_email:
            return False, "Contact has no valid email address."

        user_from = self.config.get("smtp_user", "").strip()
        from_name = self.config.get("sender_name") or self.profile.get("my_name") or "Candidate"

        # Check OAuth sender address
        use_oauth = self.is_oauth_active()
        if use_oauth:
            st = self.oauth_mgr.get_status()
            user_from = st.get("email") or user_from

        if not use_oauth and not user_from:
            return False, "Sender email not configured. Please connect Google OAuth or enter SMTP settings."

        # Find template
        tpl = next((t for t in templates if t.get("id") == template_id), None)
        if not tpl and templates:
            tpl = templates[0]
        if not tpl:
            return False, "No email template found."

        subject = render_template(tpl.get("subject", ""), contact, self.profile)
        body = render_template(tpl.get("body", ""), contact, self.profile)

        # Build MIME Message
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{from_name} <{user_from}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = user_from

        body_part = MIMEText(body, "plain", "utf-8")
        msg.attach(body_part)

        # Attach Resume if present
        if attach_resume:
            resume_rel = self.config.get("resume_path", "uploads/resume.pdf")
            resume_path = self.root_dir / resume_rel
            if resume_path.exists() and resume_path.is_file():
                try:
                    with open(resume_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=resume_path.name)
                    part["Content-Disposition"] = f'attachment; filename="{resume_path.name}"'
                    msg.attach(part)
                except Exception as e:
                    print(f"Could not attach resume: {e}")

        # Send via Google OAuth (Method 1)
        if use_oauth:
            ok, resp_msg = self.oauth_mgr.send_via_gmail_api(msg)
            status = "SENT" if ok else "FAILED"
            record_outbox_entry(
                recipient_email=to_email,
                recipient_name=contact.get("Name", "Contact"),
                company=contact.get("Company", ""),
                subject=subject,
                status=status,
                error_message=None if ok else resp_msg,
                template_id=template_id
            )
            return ok, f"Successfully sent via Google OAuth to {to_email}" if ok else resp_msg

        # Send via SMTP (Method 2)
        host = self.config.get("smtp_host", "").strip()
        port = int(self.config.get("smtp_port", 587))
        password = self.config.get("smtp_password", "").strip()
        use_ssl = self.config.get("use_ssl", False)

        if not host or not password:
            return False, "Incomplete SMTP settings. Please configure SMTP or connect Google OAuth."

        try:
            if use_ssl or port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                    server.login(user_from, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=20) as server:
                    server.ehlo()
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(user_from, password)
                    server.send_message(msg)

            record_outbox_entry(
                recipient_email=to_email,
                recipient_name=contact.get("Name", "Contact"),
                company=contact.get("Company", ""),
                subject=subject,
                status="SENT",
                template_id=template_id
            )
            return True, f"Successfully sent via SMTP to {to_email}"
        except Exception as e:
            err = str(e)
            record_outbox_entry(
                recipient_email=to_email,
                recipient_name=contact.get("Name", "Contact"),
                company=contact.get("Company", ""),
                subject=subject,
                status="FAILED",
                error_message=err,
                template_id=template_id
            )
            return False, f"Delivery failed: {err}"
