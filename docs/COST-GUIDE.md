# Cost Guide

JobSignal is designed to run for $0–12/month depending on your deployment mode and AI provider. This guide breaks down every cost component so you know exactly what you're paying for.

---

## Cost at a Glance

| Deployment | AI Tier | Monthly Cost |
|------------|---------|:---:|
| Fully Local (n8n Desktop + LM Studio) | Free (local) | **$0** |
| Self-Hosted (DigitalOcean 1GB + Google AI Studio) | Free (cloud) | **$6** |
| Self-Hosted (DigitalOcean 2GB + Google AI Studio) | Free (cloud) | **$12** |
| Self-Hosted (DigitalOcean 1GB + GPT-5 mini) | Budget | **$9–11** |
| Self-Hosted (DigitalOcean 2GB + GPT-5 mini) | Budget | **$15–17** |
| n8n Cloud Starter + Google AI Studio | Free (cloud) | **$24** |
| n8n Cloud Starter + GPT-5 mini | Budget | **$27–29** |

---

## Infrastructure Costs

### VPS (Self-Hosted Only)

| Provider | Plan | RAM | Monthly | Notes |
|----------|------|-----|:-------:|-------|
| DigitalOcean | Basic Droplet | 1GB | $6 | Core stack only (n8n + Postgres + Caddy). Cannot run both sidecars simultaneously — OOM risk. |
| DigitalOcean | Basic Droplet | 2GB | $12 | Full stack with both sidecars running 24/7. Recommended for production. |
| Hetzner | CX22 | 2GB | ~$4 | Cheapest option. EU-based data centers. |
| Vultr | Cloud Compute | 1GB | $6 | Similar to DigitalOcean. |

**What's running on the VPS:**

| Container | RAM Usage | Purpose |
|-----------|:---------:|---------|
| n8n | ~200MB | Workflow engine |
| Postgres | ~50MB | n8n's internal database |
| Caddy | ~20MB | Reverse proxy + SSL |
| cv-renderer | ~80MB | Python DOCX generation |
| jobspy-scanner | ~150MB | LinkedIn/Indeed scraping |
| **Total** | **~500MB** | Under load, spikes to ~800–960MB |

On a 1GB droplet, the total can exceed available memory when both sidecars are processing simultaneously. The OOM killer will terminate containers. Solutions: upgrade to 2GB, or stop sidecars when not in active use (`docker compose stop jobspy-scanner cv-renderer`).

### n8n Cloud

| Plan | Monthly | Executions/month | Active workflows |
|------|:-------:|:----------------:|:----------------:|
| Starter | $24 | 2,500 | 5 |
| Pro | $60 | 10,000 | Unlimited |

JobSignal uses 7 active workflows, so the Starter plan's 5-workflow limit means you'll need to prioritize (keep the 3 scanners, evaluator, and alerter active; run tailor and housekeeper manually). The Pro plan removes this constraint.

Execution count: each workflow run = 1 execution. 7 daily workflows + 1 weekly = ~50 executions/week = ~200/month. Well within Starter limits.

### n8n Desktop (Fully Local)

Free. No account required. Download from [n8n.io](https://n8n.io/get-started).

---

## AI Costs

### Google AI Studio — Gemma 4 (Free)

| Component | Cost |
|-----------|:----:|
| Job evaluations | $0 |
| Interview prep | $0 |
| CV tailoring | $0 |
| **Monthly total** | **$0** |

Google AI Studio's free tier has generous limits: 15 requests/minute and 1,500 requests/day. JobSignal's 2-second wait nodes between AI calls keep usage well within these limits. No credit card required.

### OpenAI — GPT-5 mini (Budget)

Per-job costs based on actual token usage:

| Action | Input tokens | Output tokens | Cost per job |
|--------|:------------:|:-------------:|:------------:|
| Job evaluation | ~2,000 | ~500 | ~$0.003 |
| Interview prep (High Fit only) | ~3,000 | ~2,000 | ~$0.007 |
| CV tailoring (High Fit only) | ~3,000 | ~2,000 | ~$0.008 |

Pricing at GPT-5 mini rates: $0.25 per 1M input tokens, $2.00 per 1M output tokens.

### Monthly AI cost scenarios (GPT-5 mini)

| Scenario | New jobs/day | High Fits/day | Evals/month | High Fit processing | Monthly AI cost |
|----------|:-----------:|:-------------:|:-----------:|:-------------------:|:---:|
| Light search | 10 | 1 | 300 | 30 | **~$1.35** |
| Typical search | 30 | 3 | 900 | 90 | **~$4.05** |
| Heavy search | 60 | 5 | 1,800 | 150 | **~$7.80** |

"High Fit processing" includes both interview prep ($0.007) and CV tailoring ($0.008) per High Fit job. Low and Medium Fit jobs only incur the evaluation cost ($0.003).

### Local Models — LM Studio / Ollama (Free)

| Component | Cost |
|-----------|:----:|
| Everything | $0 |
| **Monthly total** | **$0** |

Electricity and hardware amortization are the only real costs. An 8B model on a modern GPU uses ~100W during inference — pennies per job evaluation.

### OpenRouter (Variable)

Costs depend entirely on the model you choose. Check [openrouter.ai/models](https://openrouter.ai/models) for per-token pricing. Free tier models exist but are rate-limited to the point of being unusable for JobSignal.

---

## Other Service Costs

### Airtable

| Plan | Monthly | Records per base | Notes |
|------|:-------:|:----------------:|-------|
| Free | $0 | 1,000 | Works for moderate searches. Housekeeper auto-archives to manage count. |
| Team | $20/user | 50,000 | Needed if you're tracking at high volume for months |

Most users stay on the free tier. The Housekeeper (Workflow 04) archives stale Low Fit jobs weekly, keeping the record count manageable. At a typical scan volume (30 jobs/day, ~20 making it past filters), you'll accumulate ~600 records/month. Monthly archives keep you under 1,000.

**Critical:** Use a dedicated workspace for JobSignal. The 1,000 record cap is per-base within a workspace. Sharing a workspace with other bases means JobSignal competes for that limit, and writes silently fail when you hit the cap.

### Email sending

| Service | Free tier | Notes |
|---------|:---------:|-------|
| Gmail (SMTP) | Unlimited | Free with App Password. Blocked on DigitalOcean without support ticket. |
| Resend | 100 emails/day | Free. HTTP API — works everywhere. More than enough for JobSignal. |
| Discord webhook | Unlimited | Free. No email setup needed. |

JobSignal sends at most ~10 emails/day (1 digest + up to ~9 High Fit alerts on a busy day). Any free tier covers this easily.

### Domain (optional)

Only needed if self-hosting with HTTPS:

| Registrar | Annual cost | Notes |
|-----------|:-----------:|-------|
| Cloudflare | ~$10/year | Cheapest for .com |
| Namecheap | ~$10–15/year | Common choice |

Not required — you can access n8n via IP address with HTTP. A domain + Caddy gives you free SSL via Let's Encrypt.

---

## Total Cost Scenarios

### Scenario 1: "I want this completely free"

| Component | Cost |
|-----------|:----:|
| n8n Desktop | $0 |
| LM Studio + Qwen 3 8B | $0 |
| Airtable free tier | $0 |
| Gmail (SMTP) | $0 |
| **Total** | **$0/month** |

Trade-off: only runs when your laptop is on. No LinkedIn/Indeed scanning unless you also run Docker locally for the JobSpy sidecar. AI quality depends on your hardware — GPU recommended for tolerable speed.

### Scenario 2: "Always running, still free AI"

| Component | Cost |
|-----------|:----:|
| DigitalOcean 1GB Droplet | $6 |
| Google AI Studio (Gemma 4) | $0 |
| Airtable free tier | $0 |
| Resend (email) | $0 |
| **Total** | **$6/month** |

The sweet spot for most users. 24/7 scanning, free AI, all features except running both sidecars simultaneously. Run cv-renderer for DOCX generation and stop it when you want JobSpy, or upgrade to 2GB ($12/month) to run both.

### Scenario 3: "Full power, best quality"

| Component | Cost |
|-----------|:----:|
| DigitalOcean 2GB Droplet | $12 |
| OpenAI GPT-5 mini | ~$4 |
| Airtable free tier | $0 |
| Resend (email) | $0 |
| Domain (annual, amortized) | ~$1 |
| **Total** | **~$17/month** |

Everything running, highest quality AI output, DOCX CVs, LinkedIn/Indeed scanning, custom domain with SSL.

### Scenario 4: "No server management"

| Component | Cost |
|-----------|:----:|
| n8n Cloud Starter | $24 |
| Google AI Studio (Gemma 4) | $0 |
| Airtable free tier | $0 |
| Gmail (SMTP) | $0 |
| **Total** | **$24/month** |

Fastest setup, no Docker, no VPS. Trade-offs: no JobSpy (LinkedIn/Indeed), no DOCX CVs, limited to 5 active workflows on Starter plan.

---

## Cost Comparison with Alternatives

| Tool | Monthly cost | AI cost | What you get |
|------|:-----------:|:-------:|-------------|
| LoopCV | $49–149 | Included | Auto-apply, no scoring, no CV tailoring |
| LazyApply | $99 | Included | Auto-apply, gets accounts flagged |
| Teal | $9–44 | Included | Manual discovery, resume builder |
| career-ops | Free | ~$20 (Claude Pro) | CLI-based, requires active terminal |
| **JobSignal (free tier)** | **$0–6** | **$0** | **Autonomous pipeline, scoring, CV tailoring, interview prep** |
| **JobSignal (budget tier)** | **$6–17** | **$3–5** | **Same + highest quality AI output** |

---

## Monitoring Your Costs

### AI cost tracking (built in)

Every AI call in JobSignal logs its exact token cost to the Pipeline table:
- **AI Evaluation Cost** — cost of the scoring call
- **Interview Prep Cost** — cost of generating interview questions + STAR responses
- **CV Tailoring Cost** — cost of the CV rewrite

For free-tier providers (Google AI Studio, LM Studio, Ollama), these fields show $0.

### Airtable record monitoring

Check your Pipeline table record count periodically. If you're approaching 1,000 on the free tier:
1. Run the Housekeeper manually to archive stale jobs
2. Delete Archived records you no longer need
3. Consider upgrading to Airtable Team if you want to keep historical data

### VPS resource monitoring

On DigitalOcean, check your droplet's monitoring dashboard for memory usage. If you see sustained usage above 90%, you're at risk of OOM kills. Upgrade to the next tier or reduce container count.
