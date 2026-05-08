# Sigil Trinity Automation Deployment Guide

**Status:** Automated webhook system ready for deployment
**Product:** $44 recurring (initial 3 sigils + 12 monthly sigils)
**Live URL:** https://sigilcraft.thefirstspark.shop
**Intake Form:** /forge-success.html

---

## ARCHITECTURE

```
forge-success.html (intake form)
       ↓ (POST /generate)
sigil_trinity_webhook.py (Flask server)
       ├─→ sigil_trinity_generator.py (SVG generation)
       ├─→ GitHub Deploy (commit HTML to Pages)
       └─→ Resend Email (confirmation)
       
↓ (monthly cron job)
Monthly sigil generation for active subscribers
```

---

## DEPLOYMENT STEPS

### 1. ENVIRONMENT SETUP

#### Install Dependencies
```bash
pip install flask python-dotenv flask-cors
```

#### Create .env File
```bash
# .env (in sigilcraft repo root)
GITHUB_PAT=ghp_xxxxxxxxxxxxxxxxxxxxx    # GitHub personal access token
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxx # Resend API key
PORT=5000                                # Local dev; Railway sets this
```

**Get GitHub PAT:**
- Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
- Create token with `repo` scope (full control of private repos)
- Copy and paste into .env

**Get Resend API Key:**
- Sign up at resend.com
- Go to API Keys
- Create new key
- Copy and paste into .env

### 2. LOCAL TESTING

```bash
# Start webhook server locally
python sigil_trinity_webhook.py

# Should print:
# ⚡ Sigil Trinity Webhook Server starting...
#   Listening on port 5000
#   POST /generate to trigger sigil generation
```

#### Test Generation
```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Marie Lee",
    "email": "sarah@example.com",
    "dob": "1988-05-19",
    "intention": "I radiate clarity and confidence",
    "protection": "I am safe and protected",
    "manifestation": "I embody my highest self",
    "birth_location": "San Francisco, CA"
  }'
```

Expected response:
```json
{
  "success": true,
  "name": "Sarah Marie Lee",
  "message": "Sigil Trinity queued for Sarah Marie Lee — check your email in 2-3 minutes"
}
```

### 3. PRODUCTION DEPLOYMENT (Railway)

#### Create Railway Project
1. Go to railway.app
2. Create new project from GitHub
3. Connect thefirstspark/sigilcraft repo
4. Add Python service

#### Configure Environment
In Railway dashboard:
- Add variables from .env:
  - `GITHUB_PAT=ghp_...`
  - `RESEND_API_KEY=re_...`
  - `RAILWAY_ENVIRONMENT=production`

#### Deploy
- Railway auto-deploys on git push
- Public URL: `https://sigil-trinity-webhook-production.up.railway.app/generate`

### 4. WHOP INTEGRATION

#### Create Whop Product
1. Go to whop.com dashboard
2. Create product "Sigil Trinity"
   - Price: $44 USD
   - Description: "Three forged sigils + 12 monthly sigils"
3. Add promo code `TRINITYSPARK` for 30% off ($30.80)
4. Set success/webhook settings:
   - **Success URL:** `https://sigilcraft.thefirstspark.shop/forge-success.html`
   - **Webhook URL:** `https://sigil-trinity-webhook-production.up.railway.app/generate` (if using webhook from Whop)

#### Add CTA to Landing Page
In `index.html`, add card linking to:
```
<a href="https://sigilcraft.thefirstspark.shop/sigil-trinity.html">
  GET YOUR TRINITY ($44) →
</a>
```

### 5. FORM INTEGRATION

The `forge-success.html` intake form is already set up to POST to the webhook at:
- **Local dev:** `http://localhost:5000/generate`
- **Production:** `https://sigil-trinity-webhook-production.up.railway.app/generate`

**Update the webhook URL in forge-success.html (line ~350):**
```javascript
const webhookUrl = window.location.hostname === 'localhost'
  ? 'http://localhost:5000/generate'
  : 'https://sigil-trinity-webhook-production.up.railway.app/generate';
```

### 6. MANUAL FULFILLMENT TEST

To manually test the full flow:

1. **Submit intake form** (local or deployed)
2. **Check webhook logs** for generation progress
3. **Verify GitHub commit** — new folder created: `{initials}{dob}/index.html`
4. **Check Resend** — confirmation email should arrive
5. **Visit vanity URL** — e.g., `https://sigilcraft.thefirstspark.shop/sml05191988/`

---

## MONTHLY SIGIL GENERATION

Once initial Trinity is proven (5-10 sales), set up monthly regeneration:

### Option A: Cron Job (recommended)
```bash
# In production environment (Railway)
# Add monthly job via Railway's scheduler or external cron service

# Job runs: 1st of each month at 9 AM UTC
# Command: python monthly_sigil_generation.py
```

**Create `monthly_sigil_generation.py`:**
```python
from sigil_trinity_webhook import get_active_subscribers
from sigil_trinity_generator import generate_sigil_svg
from datetime import date

for subscriber in get_active_subscribers():
    name = subscriber['name']
    email = subscriber['email']
    
    # Generate new sigil based on current month
    month_theme = f"{date.today().strftime('%B %Y')}"
    svg = generate_sigil_svg(name, month_theme)
    
    # Commit to GitHub
    # Send email with new sigil
```

### Option B: Manual (until automation is proven)
Run this manually each month:
```bash
python monthly_sigil_generation.py
```

---

## TROUBLESHOOTING

### GitHub Deploy Fails
- Check `GITHUB_PAT` is set and valid
- Verify token has `repo` scope
- Check git config: `git config --list`

### Resend Email Not Sending
- Check `RESEND_API_KEY` is set
- Check email address is valid
- Verify domain is verified in Resend (should be @thefirstspark.shop)
- Check spam folder

### Form Submission Hangs
- Check webhook server is running
- Check CORS is enabled (should be by default)
- Check browser console for errors
- Increase timeout if server is slow

### SVG Sigil Generation Slow
- Generator is CPU-bound (hashing, RNG)
- Should complete in <500ms per sigil
- Profile with: `python -m cProfile sigil_trinity_generator.py`

---

## MONITORING

### Health Check
```bash
curl https://sigil-trinity-webhook-production.up.railway.app/health
# Returns: {"status": "ok", "timestamp": "2026-05-07T..."}
```

### Subscriber Database
- Location: `subscribers_trinity.json`
- Tracks: name, email, dob, purchase_date, expiry_date (12mo from purchase)
- Check periodically for subscriber count and renewals

### Logs
- Railway dashboard shows real-time logs
- Search for `[WEBHOOK]`, `[BG]`, `[EMAIL]`, `[ERROR]` tags

---

## PRICING & UPSELLS

**Sigil Trinity:** $44
- Initial 3 sigils (intention, protection, manifestation)
- 12 monthly sigils
- 12-month access to vanity URL

**Future Upsells (after 25+ sales):**
- **Sigil Grimoire** ($88) — 5 sigils + ritual binding ceremony
- **Sigil Year** ($222) — monthly sigil for 12 months (higher touch)

---

## FILES & LOCATIONS

| File | Purpose |
|---|---|
| `sigil_trinity_generator.py` | SVG sigil generation (hash + seeded RNG) |
| `sigil_trinity_webhook.py` | Flask webhook server, subscriber tracking |
| `forge-success.html` | Customer intake form |
| `template-trinity.html` | Personalized sigil page template |
| `subscribers_trinity.json` | Subscriber database |
| `index.html` | Landing page (add CTA) |
| `sigil-trinity.html` | Sales page (from PLAYBOOK) |
| `/sigils/` | Individual customer sigil folders |

---

## NEXT STEPS

1. ✅ Generator & webhook built
2. ✅ Intake form ready
3. ✅ Code committed to GitHub
4. ⏳ Deploy to Railway
5. ⏳ Configure Whop product
6. ⏳ Link from landing page
7. ⏳ Test full flow (form → generation → email → URL)
8. ⏳ Set up monthly cron job
9. ⏳ Monitor first 10 sales
10. ⏳ Upsell strategy (Grimoire, Year)

---

**Questions?** Review webhook logs, check error messages, or ask Claude.
