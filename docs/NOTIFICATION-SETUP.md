# Notification Setup

JobSignal sends two types of notifications: **High Fit alerts** (instant, from Workflow 2 when a job scores 8+) and **daily digests** (evening summary from Workflow 6). Both require an email sending method configured in n8n.

---

## Choose Your Method

| Method | Cost | Best for | SMTP? |
|--------|------|----------|:-----:|
| [**Gmail App Password**](#gmail-app-password) | Free | Most users, personal deployments | Yes (port 465) |
| [**Resend**](#resend) | Free (100/day) | DigitalOcean users, custom domains | No (HTTP API) |
| [**Discord Webhook**](#discord-webhook) | Free | Power users who live in Discord | No (HTTP API) |

**DigitalOcean users:** DigitalOcean blocks SMTP ports (465, 587) by default. Use **Resend** unless you've specifically requested SMTP unblock through their support. This is the most common notification issue on self-hosted deployments.

---

## Gmail App Password

The simplest option. Uses Gmail's SMTP server to send emails directly from your Gmail account.

### Prerequisites

- A Gmail account
- 2-Factor Authentication enabled on that account

### Step 1: Enable 2-Factor Authentication

If not already enabled:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Under "How you sign in to Google" → **2-Step Verification** → turn it on
3. Follow the prompts to add a verification method

### Step 2: Generate an App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. You may need to sign in again
3. Under "App name", type `JobSignal` (or anything — it's just a label)
4. Click **Create**
5. Google displays a 16-character password (formatted as `xxxx xxxx xxxx xxxx`)
6. **Copy this immediately** — you can't see it again after closing the dialog

### Step 3: Add the credential in n8n

1. In n8n: **Credentials** → **Add Credential** → search for **Send Email**
2. Fill in:

| Field | Value |
|-------|-------|
| SMTP Host | `smtp.gmail.com` |
| SMTP Port | `465` |
| SSL/TLS | **ON** |
| User | Your full Gmail address (e.g., `you@gmail.com`) |
| Password | The 16-character App Password from Step 2 (without spaces) |

3. Click **Save**

### Step 4: Connect to workflows

Open **Workflow 02 (Evaluator)** and **Workflow 06 (Alerter)**:

1. Find the email sending node (named "Send Email" or similar)
2. Click on it → set the credential to the one you just created
3. Set the **From** address to your Gmail
4. The **To** address is pulled automatically from your Profile table's **Notification Email** field

### Testing

Execute Workflow 06 (Alerter) manually. You should receive a daily digest email within a few seconds. Check your spam folder if it doesn't arrive — first-time sends from App Passwords sometimes land there.

---

## Resend

An HTTP-based email API. No SMTP ports needed, so it works on DigitalOcean and other VPS providers that block traditional email. Free tier sends 100 emails per day — more than enough for JobSignal.

### Step 1: Create a Resend account

1. Sign up at [resend.com](https://resend.com) — free plan works
2. Verify your email address

### Step 2: Set up a sending domain (recommended) or use the test domain

**Option A — Custom domain (recommended for production):**

1. In Resend dashboard: **Domains** → **Add Domain**
2. Enter your domain (e.g., `velocyt.ca`)
3. Add the DNS records Resend shows you (MX, SPF, DKIM) to your domain registrar
4. Wait for verification (usually 5–30 minutes)
5. Once verified, you can send from `anything@yourdomain.com`

**Option B — Test domain (quick start):**

Resend provides a shared test domain. You can send from `onboarding@resend.dev` without domain setup. Limitations: only sends to your own verified email, not suitable for production.

### Step 3: Get your API key

1. In Resend dashboard: **API Keys** → **Create API Key**
2. Name it `JobSignal`
3. Permission: **Full Access**
4. Copy the key (starts with `re_`)

### Step 4: Add the credential in n8n

1. In n8n: **Credentials** → **Add Credential** → search for **Resend**
2. Paste your API key
3. Click **Save**

### Step 5: Connect to workflows

The Evaluator (Workflow 02) and Alerter (Workflow 06) use Resend nodes:

1. Open each workflow
2. Find the Resend node
3. Set the credential to the one you just created
4. Set the **From** address to your verified domain email (e.g., `alerts@yourdomain.com`)
5. The **To** address is pulled from your Profile table's **Notification Email** field

### Resend vs Gmail in n8n

The workflows may use either a **Send Email** node (for Gmail SMTP) or a **Resend** node (for Resend API). If you're switching from one to the other:

1. Delete the existing email node
2. Add the correct node type
3. Wire it into the same position in the workflow
4. Copy the email content (subject, HTML body) from the previous node's configuration

The email HTML templates are identical regardless of method — only the sending node changes.

---

## Discord Webhook

Send notifications to a Discord channel instead of (or in addition to) email. Good if you're already living in Discord.

### Step 1: Create a webhook

1. Open your Discord server
2. Right-click the channel you want notifications in → **Edit Channel**
3. Go to **Integrations** → **Webhooks** → **New Webhook**
4. Name it `JobSignal` (or whatever you want)
5. Copy the webhook URL

### Step 2: Add an HTTP Request node in n8n

Discord webhooks are simple HTTP POST requests. In each workflow where you want Discord notifications:

1. Add an **HTTP Request** node
2. Configure it:

| Field | Value |
|-------|-------|
| Method | POST |
| URL | Your Discord webhook URL |
| Body Content Type | JSON |

3. Set the JSON body:

```json
{
  "content": "",
  "embeds": [{
    "title": "🎯 High Fit: {{ $json.jobTitle }} at {{ $json.company }}",
    "description": "Score: {{ $json.fitScore }}/10\nMatched Skills: {{ $json.matchedSkills }}",
    "url": "{{ $json.applyLink }}",
    "color": 5693273
  }]
}
```

The `color` value `5693273` is JobSignal teal (#56ABB5) in decimal.

### Step 3: Wire it into the workflow

Add the HTTP Request node after the scoring/evaluation step, in parallel with (or instead of) the email node. Use n8n's branching to send both email and Discord if you want both.

### Discord formatting tips

- Discord embeds support markdown in the `description` field
- Keep messages concise — Discord channels scroll fast
- Use the `url` field to make the embed title clickable (direct to the apply link)
- For daily digests, use multiple embeds or a single embed with a summary in the description

---

## Multiple Notification Channels

You can run email and Discord (or any combination) simultaneously:

1. After the scoring node, add a branch that splits into multiple paths
2. Each path sends to a different channel
3. All paths can run in parallel — n8n handles this natively

Common setup: email for High Fit alerts (immediate, don't want to miss), Discord for daily digests (convenient, not urgent).

---

## Troubleshooting

**Emails not arriving**
1. Check your spam/junk folder first
2. On DigitalOcean: verify SMTP isn't blocked (`telnet smtp.gmail.com 465` — if it hangs, SMTP is blocked, use Resend)
3. Check the workflow execution log in n8n — click the clock icon on the workflow to see if the email node errored

**Gmail "Less Secure App" warning**
App Passwords are not "less secure apps." If Google blocks your sign-in, make sure you're using an App Password (16-character code) and not your regular account password.

**Resend "domain not verified" error**
Your DNS records haven't propagated yet. Check in Resend dashboard → Domains → click your domain to see verification status. DNS can take up to 48 hours, though usually resolves in 5–30 minutes.

**Discord webhook "invalid URL" error**
Make sure you're using the full webhook URL (starts with `https://discord.com/api/webhooks/`). Don't truncate it.

**Emails send but contain broken HTML**
The email templates use table-based HTML for Gmail compatibility. If you've modified the HTML, test in Gmail specifically — Gmail strips many CSS properties (no `display: flex`, no `position`, limited `padding`). Stick to `<table>`, `<tr>`, `<td>` with inline styles.

---

## Email Content Reference

### High Fit Alert (Workflow 02)

Sent instantly when a job scores 8.0+:
- **Subject**: "🎯 High Fit: {Job Title} at {Company}"
- **Body**: Job title, company, location, fit score, matched skills, and a direct "Apply Now" button
- **Sender**: Your configured email address

### Daily Digest (Workflow 06)

Sent daily at 6pm (default):
- **Subject**: "📊 JobSignal Daily Digest — {date}"
- **Body**: Four sections: today's scan stats, high fit job cards with apply links, pipeline status (applied this week, active interviews), and a link to your Airtable base
- **Sender**: Your configured email address
