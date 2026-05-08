#!/usr/bin/env python3
"""
Sigil Trinity Webhook Server
============================
Receives POST requests from the intake form (forge-success.html) with customer data,
generates three sigils, personalizes the template, commits to GitHub, and sends confirmation email.

Setup:
  pip install flask python-dotenv

Environment variables:
  GITHUB_PAT=ghp_your_personal_access_token
  RESEND_API_KEY=re_your_resend_api_key

Run:
  python sigil_trinity_webhook.py
"""

import os
import sys
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from sigil_trinity_generator import (
    generate_sigil_triple,
    personalize_template,
)

SUBSCRIBERS_FILE = Path(__file__).parent / 'subscribers_trinity.json'
TEMPLATE_FILE = Path(__file__).parent / 'template-trinity.html'

app = Flask(__name__)
CORS(app, origins=["https://sigilcraft.thefirstspark.shop", "https://thefirstspark.shop"])


# ============================================================
# SUBSCRIBER MANAGEMENT
# ============================================================

def load_subscribers():
    """Load subscriber database from JSON file."""
    if SUBSCRIBERS_FILE.exists():
        try:
            with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_subscribers(subscribers):
    """Save subscriber database to JSON file."""
    with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subscribers, f, indent=2, ensure_ascii=False)


def add_subscriber(name, dob, email, extra=None):
    """Add a new subscriber (12-month Trinity subscription)."""
    subscribers = load_subscribers()

    # Check if already exists
    for sub in subscribers:
        if sub['email'] == email:
            print(f"[SUBSCRIBER] Already exists: {email}")
            return sub

    today = datetime.now()
    expiry = today + timedelta(days=365)

    subscriber = {
        'name': name,
        'email': email,
        'dob': dob,
        'purchase_date': today.isoformat(),
        'expiry_date': expiry.isoformat(),
        'active': True,
    }

    if extra:
        for key in ('intention', 'protection', 'manifestation', 'birth_location'):
            if extra.get(key):
                subscriber[key] = extra[key]

    subscribers.append(subscriber)
    save_subscribers(subscribers)

    print(f"[SUBSCRIBER] Added: {name} ({email})")
    return subscriber


def get_active_subscribers(as_of=None):
    """Get all subscribers whose 12-month window hasn't expired."""
    if as_of is None:
        as_of = datetime.now()

    subscribers = load_subscribers()
    active = []

    for sub in subscribers:
        if not sub.get('active', True):
            continue

        expiry = datetime.fromisoformat(sub['expiry_date'])
        if as_of <= expiry:
            active.append(sub)

    return active


def deactivate_subscriber(email):
    """Mark a subscriber as inactive."""
    subscribers = load_subscribers()
    for sub in subscribers:
        if sub['email'] == email:
            sub['active'] = False
            save_subscribers(subscribers)
            print(f"[SUBSCRIBER] Deactivated: {email}")
            return True
    return False


# ============================================================
# EMAIL
# ============================================================

def send_confirmation_email(recipient_email, recipient_name, sigil_url):
    """Send confirmation email via Resend API."""
    api_key = os.getenv('RESEND_API_KEY')
    if not api_key:
        print(f"[WARN] RESEND_API_KEY not set. Would send to: {recipient_email}")
        return False

    import urllib.request, urllib.error, json as _json

    html_body = f"""\
<html>
  <body style="font-family: Georgia, serif; background: #0B0B0C; color: #e0e7ff; padding: 40px 20px;">
    <div style="max-width: 700px; margin: 0 auto; border: 1px solid #6B4DF2; border-radius: 8px; padding: 40px; background: #0d0d14;">
      <h1 style="color: #F3B23A; text-align: center;">⚡ Sigil Trinity Forged</h1>
      <p style="text-align: center; color: #26E4D8; font-size: 14px; margin-bottom: 40px;">Your three sigils are live</p>
      <p>Hello <strong>{recipient_name}</strong>,</p>
      <p>The forge is complete. Your Sigil Trinity lives here:</p>
      <div style="text-align: center; margin: 40px 0;">
        <a href="{sigil_url}" style="background: linear-gradient(135deg, #F3B23A, #FF6A3D); color: #0B0B0C; padding: 16px 32px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">
          VIEW YOUR SIGILS
        </a>
      </div>
      <p style="font-size: 14px; color: #a8a8a8;">Three sigils. Forged from your name, your moment, your words.</p>
      <p style="font-size: 14px; color: #a8a8a8;">PDFs and PNGs are available on your page — print them, frame them, carry them.</p>
      <p style="font-size: 14px; color: #a8a8a8;"><strong>The 7-day activation protocol is included. Don't skip Day 7.</strong></p>
      <div style="margin-top: 50px; padding-top: 30px; border-top: 1px solid #6B4DF2; text-align: center; font-size: 12px; color: #6b7280;">
        <p><strong style="color: #F3B23A;">The First Spark</strong></p>
        <p><a href="https://thefirstspark.shop" style="color: #26E4D8;">thefirstspark.shop</a></p>
        <p style="font-style: italic;">Reality is programmable. Consciousness is the code.</p>
      </div>
    </div>
  </body>
</html>"""

    payload = _json.dumps({
        'from': 'The First Spark <hello@thefirstspark.shop>',
        'to': [recipient_email],
        'subject': f'🔥 Your Sigil Trinity is Forged — {recipient_name}',
        'html': html_body,
    }).encode()

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'TheFirstSpark-SigilTrinity/1.0',
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            print(f"[EMAIL] Sent via Resend to {recipient_email} — {r.status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Resend failed: {e.code} {e.read().decode()}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Email failed: {e}", file=sys.stderr)
        return False


# ============================================================
# GITHUB DEPLOYMENT
# ============================================================

def get_base_filename(name, dob_str):
    """Generate base filename like 'sml05191988' from name + DOB."""
    # Initials lowercase
    initials = ''.join([c for c in name if c.isupper()]).lower()
    # DOB as MMDDYYYY
    from datetime import datetime as dt
    try:
        d = dt.strptime(dob_str, '%Y-%m-%d')
        dob_fmt = f"{d.month:02d}{d.day:02d}{d.year}"
    except:
        dob_fmt = dob_str.replace('-', '')

    return f"{initials}{dob_fmt}"


def deploy_to_github(html_content, relative_path, commit_message="Sigil Trinity forged"):
    """
    Commit HTML file to GitHub.

    Args:
        html_content: HTML string
        relative_path: Path relative to repo root (e.g., "sml05191988/index.html")
        commit_message: Git commit message

    Returns:
        (success: bool, result: str)
    """
    token = os.getenv('GITHUB_PAT')
    if not token:
        return False, "GITHUB_PAT not set"

    import subprocess
    import tempfile

    repo_path = Path(__file__).parent
    file_path = repo_path / relative_path

    # Create parent directories
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path.write_text(html_content, encoding='utf-8')

    # Commit & push
    try:
        subprocess.run(['git', 'add', str(relative_path)], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_path, check=True, capture_output=True, env={**os.environ, 'GIT_TOKEN': token})

        # Return live URL
        filename = relative_path.replace('\\', '/')
        live_url = f"https://sigilcraft.thefirstspark.shop/{filename}"
        return True, live_url

    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e.stderr.decode() if e.stderr else str(e)}"
    except Exception as e:
        return False, str(e)


# ============================================================
# GENERATION WORKER
# ============================================================

def _run_generation(name, dob_str, email, intention_text, protection_text, manifestation_text, birth_location):
    """Background worker — generate sigils, personalize, commit, email."""
    try:
        print(f"\n[BG] Starting Sigil Trinity for {name}...")

        # Generate SVGs
        print(f"  [FORGE] Generating three sigils...")
        sigils = generate_sigil_triple(
            name,
            intention_text,
            protection_text,
            manifestation_text
        )

        base_filename = get_base_filename(name, dob_str)
        dob_formatted = dob_str.replace('-', '')  # YYYYMMDD -> MMDDYYYY format
        dob_mmddyyyy = f"{dob_str[5:7]}{dob_str[8:10]}{dob_str[:4]}"

        # Load and personalize template
        if not TEMPLATE_FILE.exists():
            print(f"  [ERROR] Template not found: {TEMPLATE_FILE}")
            return

        template_html = TEMPLATE_FILE.read_text(encoding='utf-8')

        first_name = name.split()[0] if name else name

        html = personalize_template(
            template_html,
            customer_name=name,
            customer_first_name=first_name,
            birth_date=dob_mmddyyyy,
            birth_location=birth_location or "",
            intention_text=intention_text,
            protection_text=protection_text,
            manifestation_text=manifestation_text,
            intention_svg=sigils['intention_svg'],
            protection_svg=sigils['protection_svg'],
            manifestation_svg=sigils['manifestation_svg'],
        )

        # Commit to GitHub
        print(f"  [GIT] Committing to GitHub...")
        success, result = deploy_to_github(
            html,
            f"{base_filename}/index.html",
            f"Sigil Trinity forged: {name}"
        )

        if success:
            live_url = result
            print(f"  [GIT] ✓ {live_url}")
        else:
            print(f"  [WARN] Deploy failed: {result}")
            live_url = None

        # Add subscriber
        add_subscriber(
            name, dob_str, email,
            extra={
                'intention': intention_text,
                'protection': protection_text,
                'manifestation': manifestation_text,
                'birth_location': birth_location,
            }
        )

        # Send email
        if email and live_url:
            print(f"  [EMAIL] Sending confirmation to {email}...")
            send_confirmation_email(email, name, live_url)

        print(f"  [BG] Done for {name} → {live_url}")

    except Exception as e:
        import traceback
        print(f"[BG ERROR] {name}: {e}", file=sys.stderr)
        traceback.print_exc()


# ============================================================
# WEBHOOK ENDPOINT
# ============================================================

@app.route('/generate', methods=['POST'])
def generate_sigil_trinity_webhook():
    """
    POST /generate

    Expected JSON:
    {
        "name": "Sarah Marie Lee",
        "email": "sarah@example.com",
        "dob": "1988-05-19",  (YYYY-MM-DD)
        "intention": "I radiate clarity and confidence",
        "protection": "I am safe and protected",
        "manifestation": "I embody my highest self",
        "birth_location": "San Francisco, CA"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['name', 'dob', 'email', 'intention', 'protection', 'manifestation']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        name = data['name'].strip()
        dob_str = data['dob'].strip()
        email = data.get('email', '').strip()
        intention = data['intention'].strip()
        protection = data['protection'].strip()
        manifestation = data['manifestation'].strip()
        birth_location = data.get('birth_location', '').strip() or None

        # Validate DOB format
        from datetime import datetime as dt
        try:
            dt.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid DOB format. Use YYYY-MM-DD'}), 400

        # Fire and forget
        t = threading.Thread(
            target=_run_generation,
            args=(name, dob_str, email, intention, protection, manifestation, birth_location),
            daemon=True
        )
        t.start()

        print(f"[WEBHOOK] Accepted {name} — generation running in background")

        return jsonify({
            'success': True,
            'name': name,
            'message': f'Sigil Trinity queued for {name} — check your email in 2-3 minutes'
        }), 200

    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# HEALTH & DEBUG
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Sigil Trinity Webhook Server',
        'endpoints': {
            'POST /generate': 'Generate Sigil Trinity from intake data',
            'GET /health': 'Health check'
        },
    }), 200


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if not os.getenv('GITHUB_PAT'):
        print("\n[WARN] GITHUB_PAT not set. Local generation only.")

    if not os.getenv('RESEND_API_KEY'):
        print("\n[WARN] RESEND_API_KEY not set. Emails won't send.")

    port = int(os.getenv('PORT', 5000))
    is_production = os.getenv('RAILWAY_ENVIRONMENT') == 'production'

    print("\n⚡ Sigil Trinity Webhook Server starting...")
    print(f"  Listening on port {port}")
    print(f"  POST /generate to trigger sigil generation\n")

    app.run(host='0.0.0.0', port=port, debug=not is_production)
