# JobSender — Automated Lead Discovery & Cold Outreach Engine

A high-performance contact discovery and cold outreach platform. Automatically source HR leads, recruiters, and decision-makers from target companies, enrich their contact details through a multi-provider waterfall, and dispatch personalized cold email sequences via **Google OAuth 2.0** or SMTP.

---

## Key Capabilities

- **Lead Discovery Waterfall**: Apollo.io, Hunter.io, SignalHire, Snov.io, RocketReach, ContactOut, and direct DNS/MX pattern prediction.
- **Modern Security & Google OAuth 2.0**: Passwordless Gmail API dispatch using official OAuth 2.0 scopes (`gmail.send` & `userinfo.email`), automatic token refresh, and HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`).
- **Dynamic Multi-Link Profile**: Candidate profile management with an interactive `+ Add New Link` action button for custom labeled URLs (Portfolio, LinkedIn, GitHub, LeetCode, Calendly, etc.).
- **Smart Template Engine**: Dynamic variable interpolation (`{{First_Name}}`, `{{Company}}`, `{{Role}}`, `{{All_Links}}`, custom link tags), live message preview, and PDF resume attachments.
- **Google Sheets 2-Way Sync**: Import company domains or export enriched leads directly to Google Sheets with real-time feedback.
- **Modern B2B SaaS Dashboard**: Dark-mode console with live Socket.IO pipeline streaming, lead filtering, search, and outbox logs.

---

## Architecture Overview

```
JobSender/
├── dashboard/               # Flask + Socket.IO web console (127.0.0.1:5000)
│   ├── app.py              # REST API & WebSocket handlers
│   └── templates/
│       └── index.html      # Monolithic B2B SaaS dashboard UI
├── outreach/                # Outreach & delivery engine
│   ├── google_oauth.py     # Google OAuth 2.0 & Gmail REST API manager
│   ├── sender.py           # Hybrid email dispatcher (OAuth 2.0 + SMTP)
│   └── templates.py        # Variable interpolation & template management
├── integrations/            # External service connectors
│   └── google_sheets.py    # Google Sheets API v4 import & export sync
├── scrapers/                # Web scraping and directory crawlers
├── enrichers/               # Multi-tool contact waterfall & email verification
├── pipeline.py              # Lead discovery and enrichment orchestrator
├── scheduler.py             # Automated recurring job scheduler
├── main.py                  # CLI entry point (run, dashboard, schedule)
└── config.yaml              # Local configuration & provider credentials
```

---

## Quick Start

### 1. Prerequisites & Installation

```bash
# Clone the repository
git clone https://github.com/Visshu78/Job_seeker.git
cd Job_seeker

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings
Copy `config.example.yaml` to `config.yaml` and add any API keys you wish to use (Apollo, Hunter, etc.):
```bash
cp config.example.yaml config.yaml
```

### 3. Launch Web Dashboard
```bash
python main.py dashboard
# Web console starts at http://127.0.0.1:5000
```

### 4. Or Run Headless via CLI
```bash
# Run with inline companies
python main.py run --companies "Google, Stripe, Airbnb"

# Run from CSV list
python main.py run --input input/companies_sample.csv
```

---

## Email Outreach & Authentication

### Option A: Google OAuth 2.0 (Recommended)
1. Open the dashboard at `http://127.0.0.1:5000` and click **Email Outreach**.
2. Under **Outreach Authentication & Security**, provide your Google OAuth Client ID & Secret, or upload `client_secret.json`.
3. Set your Google Cloud Console Authorized Redirect URI to:
   ```text
   http://127.0.0.1:5000/api/auth/google/callback
   ```
4. Click **Connect with Google** to authorize. All cold emails will be sent securely via Gmail REST API.

### Option B: SMTP Fallback
Switch to the **SMTP Fallback** tab and provide your SMTP Host (`smtp.gmail.com`), Port (`587`), email address, and 16-character [Google App Password](https://myaccount.google.com/apppasswords).

---

## Security & Compliance
- **Local Loopback**: Dashboard strictly binds to `127.0.0.1` to prevent unauthorized network exposure.
- **HTTP Security Headers**: Hardened with `nosniff`, `SAMEORIGIN`, and `1; mode=block`.
- **Credential Safety**: OAuth tokens and API secrets are stored locally on your machine and excluded from git tracking.
