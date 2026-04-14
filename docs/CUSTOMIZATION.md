# Customization Guide

> 🚧 **Coming soon** — How to customize JobSignal for your specific profile and target roles.

## Quick Tips

### Adding Companies

Add rows to the **Tracked Companies** table in Airtable:
- Set **Company Name**, **API Endpoint**, and **Scan Method** (Greenhouse API, Ashby, or Lever)
- Toggle **Enabled** to true
- The next scanner run will pick it up automatically

### Testing a Greenhouse Endpoint

```
curl https://boards-api.greenhouse.io/v1/boards/{company-slug}/jobs
```

If it returns `{"jobs":[],"total":0}` — the endpoint works, just no matching jobs right now. If it returns 404 — wrong slug.

### Title Keywords

Add comma-separated keywords to the **Title Keywords** column in Tracked Companies to filter by job title. Leave blank to see all roles at that company.

### Tuning AI Scoring

Edit the **Scoring Rubric Override** field in your Profile table to add custom instructions that get appended to the AI scoring prompt.
