# Setup Guide

Complete walkthrough for getting JobSignal Engine running. Pick your deployment mode, follow the steps, and you'll have an autonomous job search pipeline in 30–60 minutes.

---

## Choose Your Deployment Mode

| Mode | Best for | Monthly cost | LinkedIn/Indeed? | DOCX CVs? | 24/7? |
|------|----------|:---:|:---:|:---:|:---:|
| [**Self-Hosted**](#self-hosted-setup) | Full power, always running | $12 | ✅ | ✅ | ✅ |
| [**Fully Local**](#fully-local-setup) | $0 total, privacy-first | $0 | ✅ | ✅ | ❌ |
| [**n8n Cloud**](#n8n-cloud-setup) | Already paying for n8n Cloud | €20+ | ❌ | ❌ (text only) | ✅ |

All three modes support Greenhouse/Ashby/Lever scanning, AI scoring, interview prep, email alerts, and daily digests. The differences are in job board scraping (LinkedIn/Indeed require the JobSpy sidecar), CV file generation (DOCX requires the cv-renderer sidecar), and whether the system runs 24/7 or only when your machine is on.

---

## Prerequisites (All Modes)

Before starting any deployment mode, you need:

1. **An Airtable account** — free tier works. Sign up at [airtable.com](https://airtable.com).
2. **An AI provider API key** — Google AI Studio is free. See [AI-PROVIDERS.md](AI-PROVIDERS.md) for all options.
3. **An email sending method** — Gmail App Password or Resend API key. See [NOTIFICATION-SETUP.md](NOTIFICATION-SETUP.md).

---

## Step 1: Set Up Airtable (All Modes — 10 minutes)

This is the same regardless of deployment mode.

### 1.1 Create a dedicated workspace

Airtable's free tier caps at 1,000 records per base. Create a new workspace called **Job Engine Workspace** and keep it separate from your other bases. If you share a workspace, JobSignal's writes will silently fail once you hit the cap.

### 1.2 Create the base

Create a new base called **Job Signal Engine** inside that workspace.

### 1.3 Import tables from CSV templates

The `airtable/templates/` folder in the repo contains CSV files for each table. Import them in this order:

1. **Profile** — `profile-template.csv`
2. **Tracked Companies** — `tracked-companies-template.csv` (pre-loaded with 139 verified companies)
3. **Pipeline** — `pipeline-template.csv`
4. **Search Queries** — `search-queries-template.csv` (only needed if using JobSpy)

To import: in your base, click **+** to add a table → **Import data** → **CSV file** → select the template.

After importing, you'll need to adjust field types. See [`AIRTABLE-SCHEMA.md`](../airtable/AIRTABLE-SCHEMA.md) for the exact type each field should be (Single Select, Multiple Select, Checkbox, Number, etc.). The CSV import creates everything as text — you need to convert the fields manually.

### 1.4 Fill in your Profile

Open the **Profile** table and fill in your single row. Every field matters — this is what the AI scores against:

| Field | What to enter | Why it matters |
|-------|---------------|----------------|
| Full Name | Your name | Used in CV generation and interview prep |
| Professional Summary | 2–3 sentences positioning yourself | Injected directly into AI scoring prompts |
| Core Skills | Your primary technical skills | 40% of the scoring weight |
| Secondary Skills | Supporting/adjacent skills | Partial credit in scoring |
| Target Roles | Job titles you're pursuing | 25% of scoring weight |
| Target Industries | Preferred industries | 10% of scoring weight |
| Negative Filters | Hard exclusions (Junior, PHP, Blockchain, etc.) | Auto-caps score at 3.0 if matched |
| Seniority Level | Mid, Senior, Staff, Lead, or Head | 15% of scoring weight |
| Location Preference | Remote Only, Hybrid, On-site, or Any | 10% of scoring weight |
| Target Geography | Countries/regions to accept | Scanner filters by this |
| CV Markdown | Your full CV in markdown format | **Critical** — without this, tailored CVs and STAR responses are generic |
| Notification Email | Where alerts and digests go | Used by Workflows 2 and 6 |
| AI Model | Model string (e.g., `gemma-4-26b-a4b-it`) | Informational only — the actual model is set in each n8n OpenAI node (see AI-PROVIDERS.md) |

**Tip:** The CV Markdown field is the single most important field for output quality. Paste your entire CV as markdown — include project names, company names, tools used, and quantifiable outcomes. The interview prep and CV tailoring prompts inject this directly, so the more specific your CV, the more specific the AI's output.

### 1.5 Get your Airtable Personal Access Token

1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Click **Create new token**
3. Name it `JobSignal`
4. Scopes: `data.records:read`, `data.records:write`
5. Access: add your **Job Signal Engine** base
6. Click **Create token** and copy it — you'll need it in n8n

### 1.6 Note your Base ID and Table IDs

You'll need these for the workflow configurations:

- **Base ID**: Open your base in Airtable. The URL looks like `airtable.com/appXXXXXXXXXXXXX/...` — the `appXXXXXXXXXXXXX` part is your Base ID.
- **Table IDs**: Click on each table name, check the URL for `tblXXXXXXXXXXXXX`.

You'll need the Pipeline table ID and (if using JobSpy) the Search Queries table ID when configuring workflows.

---

## Self-Hosted Setup

The full-power deployment. Runs 24/7 on a VPS with all features including LinkedIn/Indeed scanning and DOCX CV generation.

### 2.1 Provision a VPS

**DigitalOcean** (recommended — tested in production):

- Create a Droplet: Ubuntu 24.04, **2GB RAM / 1 vCPU** (~$12/month)
- This is the minimum for running the full stack with both sidecars simultaneously (n8n + Postgres + Caddy + JobSpy + cv-renderer)
- A 1GB droplet (~$6/month) runs the core stack (n8n + Postgres + Caddy) but OOM-kills if you run both sidecars at once. Only choose 1GB if you're comfortable stopping sidecars on demand
- Add your SSH key during creation

Other VPS providers work fine — Hetzner (CX22, ~€3.50), Vultr, Linode. You just need Docker and Docker Compose support.

*VPS pricing as of April 2026 — verify current rates with your provider.*

### 2.2 Install Docker

SSH into your server and install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

Verify Docker Compose is available (the script installs it by default on Ubuntu 24.04, but verify):

```bash
docker compose version
```

If the command returns "not a docker command," install the Compose plugin:

```bash
sudo apt install docker-compose-plugin -y
```

### 2.3 Clone the repo and configure

```bash
cd ~
git clone https://github.com/RZ-Logic/jobsignal-engine.git
cd jobsignal-engine

# Copy the example compose file
cp docker-compose.example.yml docker-compose.yml
```

Edit `docker-compose.yml` and set your environment variables:

```bash
nano docker-compose.yml
```

Key variables to configure in the n8n service:

```yaml
environment:
  - N8N_BASIC_AUTH_USER=your-username        # n8n login username
  - N8N_BASIC_AUTH_PASSWORD=your-password     # n8n login password
  - N8N_HOST=your-domain.com                 # your domain (if using Caddy)
  - N8N_PROTOCOL=https
  - GENERIC_TIMEZONE=America/Toronto          # Set to YOUR timezone
  - DB_TYPE=postgresdb
  - DB_POSTGRESDB_HOST=postgres
  - DB_POSTGRESDB_DATABASE=n8n
  - DB_POSTGRESDB_USER=n8n
  - DB_POSTGRESDB_PASSWORD=your-db-password
```

**Timezone matters.** n8n's schedule triggers fire based on the server timezone. If you leave it as UTC, your "8am scan" runs at 8am UTC (3am EST). Set `GENERIC_TIMEZONE` to your local timezone.

### 2.4 Start the stack

```bash
docker compose up -d
```

This starts n8n, Postgres, Caddy, and both sidecar containers. Verify everything is running:

```bash
docker compose ps
```

You should see 5 containers: `n8n`, `postgres`, `caddy`, `cv-renderer`, `jobspy-scanner`.

Access n8n at `https://your-domain.com` (if using Caddy with a domain) or `http://your-server-ip:5678`.

### 2.5 Import workflows

In n8n:

1. Go to **Settings** (gear icon) → click the **...** menu → **Import from File**
2. Import each JSON file from the `workflows/` folder, in this order:
   - `01a-scanner-greenhouse.json`
   - `01b-scanner-ashby.json`
   - `01c-scanner-lever.json`
   - `01d-scanner-jobspy.json`
   - `02-evaluator.json`
   - `03-tailor.json`
   - `04-housekeeper.json`
   - `06-alerter.json`

### 2.6 Configure credentials in n8n

You need to set up credentials that the workflows reference:

**Airtable credential:**
1. In n8n: **Credentials** → **Add Credential** → search **Airtable Personal Access Token**
2. Paste your PAT from Step 1.5

**AI provider credential:**
1. **Credentials** → **Add Credential** → search **OpenAI API**
2. Set the **API Key** to your provider's key
3. Set the **Base URL** to your provider's endpoint (see [AI-PROVIDERS.md](AI-PROVIDERS.md))
4. This single credential is used by all AI workflows — Evaluator, Interview Prep, and Tailor

**Email credential:**

JobSignal ships with **Resend** nodes by default (works on any host, bypasses SMTP port blocks). To use Resend:
1. **Credentials** → **Add Credential** → search **Resend**
2. Paste your Resend API key (get one free at [resend.com](https://resend.com))

**Prefer Gmail?** Gmail SMTP works on n8n Desktop and most self-hosted setups (except DigitalOcean, which blocks SMTP ports). If you want Gmail instead of Resend, see [NOTIFICATION-SETUP.md](NOTIFICATION-SETUP.md) for how to swap the Resend nodes to Send Email nodes in the workflows.

**Header Auth credential (for CV attachment upload):**
1. **Credentials** → **Add Credential** → search **Header Auth**
2. Name: `Authorization`
3. Value: `Bearer YOUR_AIRTABLE_PAT`

This is used by Workflow 3 (Tailor) to upload DOCX files directly to Airtable records.

### 2.7 Update workflow references

Each workflow references specific Airtable base IDs, table IDs, and credentials. Open each workflow and verify:

- All **Airtable** nodes point to your base and tables (not the original developer's)
- All **OpenAI** nodes use your AI credential
- All **Send Email** / **Resend** nodes use your email credential
- Workflow 3's **HTTP Request** node (CV upload) uses your Header Auth credential

**Tip:** The fastest way to do this is to open each workflow, click on any Airtable node, and update the credential + base + table selections. n8n will prompt you to update them when credentials don't match.

### 2.8 Test each workflow manually

Before activating schedules, test each workflow by clicking **Execute Workflow**:

1. **01a-scanner-greenhouse** — should fetch jobs and create Pipeline records
2. **02-evaluator** — should score any New jobs (run after scanner creates some)
3. **03-tailor** — should generate CVs for High Fit jobs
4. **06-alerter** — should send a daily digest email
5. **04-housekeeper** — should report on stale jobs (safe to run anytime)

### 2.9 Activate schedules

Once testing passes, toggle each workflow to **Active**. The default schedule:

| Workflow | Schedule | Time |
|----------|----------|------|
| 01a — Greenhouse Scanner | Daily | 8:00 AM |
| 01b — Ashby Scanner | Daily | 8:05 AM |
| 01c — Lever Scanner | Daily | 8:10 AM |
| 01d — JobSpy Scanner | Daily | 8:15 AM |
| 02 — Evaluator | Daily | 9:00 AM |
| 03 — Tailor | Daily | 9:30 AM |
| 04 — Housekeeper | Weekly | Sunday midnight |
| 06 — Alerter | Daily | 6:00 PM |

These times are based on your `GENERIC_TIMEZONE` setting. Adjust in each workflow's Schedule Trigger node if needed.

---

## n8n Cloud Setup

The fastest path — no server to manage. You lose JobSpy (LinkedIn/Indeed scraping) and DOCX CV generation, but everything else works.

### 3.1 Sign up for n8n Cloud

Go to [n8n.io](https://n8n.io) and create an account. The Starter plan (€20/month, ~$22 USD) works — it includes unlimited workflows and 2,500 executions/month, which is well above JobSignal's typical usage (~200–300 executions/month).

*Pricing as of April 2026 — verify at [n8n.io/pricing](https://n8n.io/pricing).*

### 3.2 Import workflows

Same as Step 2.5, but **skip `01d-scanner-jobspy.json`** — JobSpy requires a sidecar container that n8n Cloud can't run.

Import the other 7 workflows.

### 3.3 Configure credentials

Same as Step 2.6, but:

- Skip the Header Auth credential (no DOCX upload on Cloud)
- The Tailor workflow (03) will still generate tailored CV text and save it to the Pipeline's **Tailored CV Text** field — you just won't get a DOCX file attachment

### 3.4 Update references, test, and activate

Same as Steps 2.7–2.9.

**n8n Cloud timezone note:** n8n Cloud uses UTC by default. Adjust your Schedule Trigger times to account for the offset. If you're in EST (UTC-4), set your "8am" scanner to fire at 12:00 PM in the Schedule Trigger to get 8am local time.

---

## Fully Local Setup

Zero cost, maximum privacy. Runs on your machine using n8n Desktop + LM Studio (or Ollama) for local AI inference. Only runs when your laptop is on.

### 4.1 Install n8n Desktop

Download from [n8n.io/get-started](https://n8n.io/get-started). Available for macOS, Windows, and Linux. Free, no account required.

### 4.2 Install a local AI provider

**Option A — LM Studio (recommended, GUI):**
1. Download from [lmstudio.ai](https://lmstudio.ai)
2. Search for and download a model (recommended: Qwen 3 8B or Llama 3.2)
3. Go to the **Local Server** tab → click **Start Server**
4. Server runs at `http://localhost:1234/v1`

**Option B — Ollama (CLI):**
1. Install from [ollama.com](https://ollama.com)
2. Pull a model: `ollama pull qwen3:8b`
3. Server runs automatically at `http://localhost:11434/v1`

### 4.3 Import workflows and configure

Same as the self-hosted setup (Steps 2.5–2.7), with these differences:

- **AI credential Base URL**: set to `http://localhost:1234/v1` (LM Studio) or `http://localhost:11434/v1` (Ollama)
- **AI credential API Key**: set to `lm-studio` (LM Studio) or `ollama` (Ollama) — these are dummy values, local servers don't require real keys
- **JobSpy**: you can run the JobSpy sidecar locally with Docker if you have it installed:
  ```bash
  cd jobsignal-engine
  docker build -f scripts/Dockerfile.jobspy -t jobspy-scanner .
  docker run -d -p 3457:3457 jobspy-scanner
  ```
- **CV Renderer**: same approach:
  ```bash
  docker build -f scripts/Dockerfile.cv-renderer -t cv-renderer .
  docker run -d -p 3456:3456 cv-renderer
  ```

### 4.4 Adjust schedule expectations

n8n Desktop only runs when your machine is on. Workflows fire on their schedule, but if your laptop is asleep at 8am, the scan runs when you open it next. This is fine for most users — you just won't get results "before you wake up."

---

## Verifying Your Setup

After completing any deployment mode, run this checklist:

1. **Scanner test**: Execute Workflow 01a manually. Check your Pipeline table — do new jobs appear with Status: New?
2. **Evaluator test**: Execute Workflow 02. Do the New jobs now have scores, fit tiers, and reasoning?
3. **Alert test**: If any job scored High Fit, did you receive an email?
4. **Digest test**: Execute Workflow 06. Did you receive a daily digest email?
5. **Tailor test** (self-hosted/local only): Execute Workflow 03. Do High Fit jobs now have a DOCX attachment in the Tailored CV field?

If any step fails, check the workflow's execution log in n8n (click the clock icon on the workflow). The error message will tell you which node failed and why.

---

## Common Issues

**"No items" in scanner output**
Your Tracked Companies table might be empty or all entries are disabled. Check that at least some companies have Enabled = true and a valid API Endpoint.

**Airtable "AUTHENTICATION_REQUIRED" error**
Your PAT is missing or expired. Regenerate it and update the credential in n8n.

**AI node returns empty or garbled output**
If using Gemma 4, LM Studio, Ollama, or any open-source model: make sure **Output Content as JSON** is toggled **OFF** in each OpenAI node's settings. The system prompts enforce JSON output directly. This isn't needed for GPT-5 mini — only open-source and local models.

**Emails not sending on DigitalOcean**
DigitalOcean blocks SMTP ports (465, 587) by default. Use Resend (HTTP API) instead, or open a DigitalOcean support ticket to request SMTP unblock. See [NOTIFICATION-SETUP.md](NOTIFICATION-SETUP.md).

**OOM kills on 1GB droplet**
Running all 5 containers (n8n + Postgres + Caddy + JobSpy + CV renderer) exceeds ~960MB. Either upgrade to 2GB ($12/month) or stop the sidecars when not in use:
```bash
docker compose stop jobspy-scanner cv-renderer
```

**Schedule triggers firing at wrong times**
n8n uses the server's timezone. Check your `GENERIC_TIMEZONE` environment variable matches your local timezone. On n8n Cloud, schedules are UTC — offset manually.

---

## Next Steps

- [AI-PROVIDERS.md](AI-PROVIDERS.md) — Configure your AI tier (free, budget, or local)
- [CUSTOMIZATION.md](CUSTOMIZATION.md) — Add companies, tune keywords, adjust scoring
- [NOTIFICATION-SETUP.md](NOTIFICATION-SETUP.md) — Set up Gmail, Resend, or Discord
- [COST-GUIDE.md](COST-GUIDE.md) — Understand exactly what you're paying for
- [AIRTABLE-SCHEMA.md](../airtable/AIRTABLE-SCHEMA.md) — Full field reference for every table
