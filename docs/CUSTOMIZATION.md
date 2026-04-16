# Customization Guide

JobSignal is configured entirely through Airtable — no workflow edits needed for personalization. This guide covers how to add companies, tune title keywords, adjust AI scoring, configure geography filters, and optimize the system for your specific job search.

---

## Adding Companies to Track

The **Tracked Companies** table controls which companies get scanned daily. The repo ships with 139 verified companies across 30 categories (AI/ML, DevTools, FinTech, SaaS, Cloud, Security, and more). You can add any company that uses Greenhouse, Ashby, or Lever for their job board.

### Finding a company's ATS and endpoint

Most tech companies use one of three ATS platforms with public APIs:

**Greenhouse** (~40% of tech companies):
```bash
curl -s https://boards-api.greenhouse.io/v1/boards/{company-slug}/jobs | head -c 200
```
Replace `{company-slug}` with the company name in lowercase, sometimes with hyphens. Common patterns: `stripe`, `airtable`, `anthropic`, `vercel`. If you get a JSON response with a `jobs` array, the endpoint works. If you get a 404, try variations (e.g., `openai` vs `open-ai`) or check their careers page source code for the slug.

A response of `{"jobs":[],"total":0}` means the endpoint is valid — the company just has no open jobs right now. That's not broken.

**Ashby** (~30% of tech startups, growing):
```bash
curl -s "https://api.ashbyhq.com/posting-api/job-board/{company-slug}?includeCompensation=true" | head -c 200
```
Common slugs: `n8n`, `cohere`, `elevenlabs`, `perplexity`, `runway`, `langchain`, `replit`. Ashby is now the dominant ATS for AI/ML startups — if a company isn't on Greenhouse, try Ashby first.

**Lever** (~15% of tech companies, declining):
```bash
curl -s "https://api.lever.co/v0/postings/{company-slug}" | head -c 200
```
Lever has thin coverage in the AI/tech space. Most companies have migrated to Ashby. Confirmed working: `mistral`, `plaid`.

**Not supported (no public APIs):** Workday, Taleo, iCIMS, SmartRecruiters, BambooHR. These are used by enterprise companies (banks, consulting firms, Big 4) and don't expose public JSON endpoints. JobSpy partially covers these via LinkedIn/Indeed scraping.

### Adding a company to the Tracked Companies table

Once you've verified the endpoint, add a row:

| Field | Value |
|-------|-------|
| Company Name | The company's name (e.g., `Notion`) |
| API Endpoint | The full verified URL |
| Scan Method | `Greenhouse API`, `Ashby API`, or `Lever API` |
| Title Keywords | Optional — comma-separated filter terms (see below) |
| Enabled | ✅ (checked) |

The next scanner run automatically picks up new companies. No workflow restart needed.

### Contributing companies back

Found a working endpoint? Submit a PR to add it to `companies-default.csv`. Include the company name, verified API endpoint, scan method, and category. The CSV format:

```csv
Company Name,API Endpoint,Scan Method,Category
Notion,https://api.ashbyhq.com/posting-api/job-board/notion?includeCompensation=true,Ashby API,Productivity
```

---

## Tuning Title Keywords

Title Keywords in the Tracked Companies table filter which jobs pass through to your Pipeline. This prevents irrelevant roles from consuming AI evaluation credits and cluttering your dashboard.

### How filtering works

The scanner checks if any keyword appears as a **case-insensitive substring** in the job title. If the Title Keywords field is blank, all roles at that company pass through.

### Best practices

**Use compound terms, not single words.** Single words match too broadly:

| Keyword | Problem |
|---------|---------|
| `engineer` | Matches "Civil Engineer", "Audio Engineer", "Sales Engineer" |
| `automation` | Matches "Building Automation (HVAC)", "Test Automation" |
| `ai` | Matches "Air Quality", "AICS Coordinator" |

Better:

```
ai engineer, ai automation, automation engineer, solutions architect,
solutions engineer, implementation engineer, forward deployed,
gtm engineer, go-to-market, revops, platform engineer
```

**Leave blank for companies where you'd want any role.** If a company is small and highly aligned (e.g., n8n, LangChain), leave Title Keywords empty to see all openings.

**Be generous rather than restrictive.** The AI Evaluator is the precision filter — it scores every job against your full profile. Title Keywords are just the coarse filter to keep volume manageable. If a borderline role slips through, the Evaluator will score it Low Fit and it'll be archived automatically by the Housekeeper.

---

## Adjusting AI Scoring

The Evaluator uses a weighted rubric to score jobs 1–10:

| Criterion | Weight | What it measures |
|-----------|:------:|------------------|
| Skill Match | 40% | How many of your Core Skills does the JD require? Partial credit for Secondary Skills |
| Role Alignment | 25% | Does the title/function match your Target Roles? |
| Seniority Fit | 15% | Is the level appropriate for your Seniority Level? |
| Industry/Domain | 10% | Does the company/industry match your Target Industries? |
| Location Match | 10% | Does the role meet your Location Preference and Target Geography? |

### Automatic disqualifiers

These cap the score at 3.0 regardless of other criteria:
- The JD primarily requires skills in your Negative Filters list
- The role is a fundamentally different function than your Target Roles
- The role is junior/intern level when you're Senior+

### Customizing the rubric

The **Scoring Rubric Override** field in your Profile table lets you append custom instructions to the AI scoring prompt. This is free-form text that gets injected after the default rubric.

**Example overrides:**

Boost scores for specific companies:
```
Give +1 bonus to companies in the AI/ML infrastructure space
(LangChain, Anthropic, OpenAI, Cohere, ElevenLabs, Hugging Face).
These are priority targets.
```

Penalize specific patterns:
```
Score down by 2 points any role that requires 7+ years of experience
in a single technology. These tend to be poor-fit rigid requirements.
```

Add domain-specific criteria:
```
If the JD mentions "workflow automation", "process automation",
or "business process" in the core requirements, add +1 to the
Skill Match score. These are high-signal terms for this candidate.
```

Adjust for market conditions:
```
For roles in Canada, be more lenient on industry alignment —
the Canadian tech market is smaller and cross-industry moves
are more common. Score Industry/Domain at half weight for
Canadian positions.
```

**Be specific.** Vague overrides like "be more generous" or "score higher" produce inconsistent results. Tell the AI exactly what to look for and how to adjust.

---

## Configuring Geography Filters

The **Target Geography** field in your Profile table controls which countries/regions the scanners accept jobs from. This is a multi-select field with pre-defined options:

| Geography value | What it matches |
|-----------------|-----------------|
| Canada | Jobs located in Canada, Canadian cities |
| USA | Jobs located in the United States |
| Remote Global | Remote roles with no location restriction |
| Remote North America | Remote roles restricted to NA timezones |
| EMEA | Europe, Middle East, Africa |
| UK | United Kingdom specifically |
| APAC | Asia-Pacific |

### How geography filtering works

Each scanner's Parse & Filter node reads your Target Geography from the Profile table and matches it against the job's location field. The matching is fuzzy — it checks for country names, city names, region terms, and common patterns like "Remote" or "Anywhere."

**Important:** LinkedIn and Indeed (via JobSpy) often return "Not specified" as the location. The scanner passes these through intentionally — many remote roles don't have structured location data. The Evaluator then checks location fit as part of scoring, so truly mismatched jobs get scored low.

### Adding custom geography values

If you need regions not in the default list:

1. Open your Profile table in Airtable
2. Click the Target Geography field → **Customize field type**
3. Add new options (e.g., `Germany`, `Singapore`, `Latin America`)
4. The scanner's geography matching uses substring checks, so the value you add should appear in job location strings

---

## Configuring JobSpy Searches (Self-Hosted Only)

The **Search Queries** table controls what JobSpy searches for on LinkedIn and Indeed.

### Adding a search query

| Field | Value | Notes |
|-------|-------|-------|
| Query Name | Human label (e.g., "AI Automation — Remote") | For your reference only |
| Search Term | The search string (e.g., "AI automation engineer") | What gets sent to LinkedIn/Indeed |
| Sites | Comma-separated list (e.g., `linkedin,indeed`) | Which job boards to search |
| Location | Geographic filter (e.g., "Canada" or blank for remote) | Passed to the job boards |
| Results Wanted | Number per site (e.g., `30`) | Per-site, not total — 30 across 3 sites = up to 90 results |
| Country Indeed | Indeed-specific country code (e.g., `canada`) | Only used by Indeed, ignored by LinkedIn |
| Title Keywords | Comma-separated filter terms | Applied after results come back |
| Enabled | ✅ | Toggle without deleting |

### Query optimization tips

- **LinkedIn rate limits around page 10.** Keep Results Wanted ≤ 50 per query to avoid rate limiting.
- **Indeed searches description text**, not just titles. You may get unrelated roles that mention your keywords in the job description. The Title Keywords filter catches these.
- **Glassdoor returns 0 results** (403 blocked as of April 2026). Don't include it in Sites — it's not worth debugging.
- **`linkedin_fetch_description=true`** is set in the JobSpy sidecar code. Without this, LinkedIn returns "Not specified" for location and null for descriptions. Already configured; no action needed.

---

## Customizing the CV Template

The Tailor workflow (03) generates CVs using a Python sidecar. The output styling is defined in `scripts/render_cv.py`.

### Current design

- **Font**: Calibri throughout
- **Section headers**: Teal (#56ABB5) text with dark grey (#333333) bottom border
- **Layout**: Single-column, ATS-optimized (no tables, no graphics, no columns)
- **Output**: Standard DOCX file attached to the Airtable record

### Modifying the template

To change fonts, colors, or layout:

1. Edit `scripts/render_cv.py` on your server
2. The file is volume-mounted in Docker — changes take effect without rebuilding the container
3. Key variables:
   - Header color: search for `RGBColor` calls
   - Font: search for `font.name`
   - Spacing: search for `paragraph_format.space_before` / `space_after`

### Important: keep it ATS-friendly

Automated Tracking Systems parse DOCX files. Avoid tables, text boxes, graphics, multi-column layouts, and custom fonts. Simple, clean, single-column formatting passes ATS parsers reliably.

---

## Adjusting Workflow Schedules

The default schedule is optimized for a morning scan + evening digest cycle:

| Workflow | Default | When to change |
|----------|---------|----------------|
| Scanners (01a–01d) | 8:00–8:15 AM | If you want scans at a different time |
| Evaluator (02) | 9:00 AM | Must run after scanners complete |
| Tailor (03) | 9:30 AM | Must run after evaluator completes |
| Housekeeper (04) | Sunday midnight | Weekly is fine for most volumes |
| Alerter (06) | 6:00 PM | Change to whenever you want your daily summary |

To change: open the workflow in n8n → click the **Schedule Trigger** node → adjust the time.

**Critical dependency:** The Evaluator must run after scanners finish, and the Tailor must run after the Evaluator. If you move the scanner times, adjust the others to maintain the sequence.

**Timezone reminder:** Self-hosted n8n uses the `GENERIC_TIMEZONE` environment variable. n8n Cloud uses UTC. See [SETUP.md](SETUP.md) for details.

---

## Tuning for Volume

### Low volume (5–15 jobs/day)

The default settings work well. 139 tracked companies across Greenhouse/Ashby/Lever typically yield 5–15 new relevant jobs daily, depending on your keywords.

### High volume (50+ jobs/day)

If you're tracking many companies or using broad keywords:

- **Tighten Title Keywords** — add keywords to high-volume companies to reduce noise
- **Safety brakes are already set** — scanners cap at 100–200 jobs per run to prevent runaway processing
- **Monitor Airtable record count** — the free tier caps at 1,000 records. The Housekeeper archives stale Low Fit jobs weekly, but at high volume you may need to archive more aggressively or upgrade Airtable
- **AI rate limits** — Google AI Studio's 15 RPM handles the typical JobSignal workload easily (~500 new jobs/day in normal use). If you're consistently hitting 50+ new jobs daily with many High Fits triggering interview prep and CV tailoring, consider OpenAI (no practical rate limit at this volume)

### Minimal volume (testing / occasional use)

Disable most tracked companies and keep only 5–10 target companies enabled. Run scanners manually instead of on a schedule. This is useful during setup or when you're between active job searches.
