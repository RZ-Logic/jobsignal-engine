# AI Providers Guide

JobSignal uses a single OpenAI-compatible credential in n8n. Every AI workflow — scoring, interview prep, CV tailoring — inherits from this one credential. Switching providers means changing two fields (Base URL + API Key) and nothing else. No workflow edits, no prompt changes, no node swaps.

---

## Provider Tiers

| Tier | Provider | Model | Base URL | Cost | Best for |
|------|----------|-------|----------|------|----------|
| **Free (cloud)** | Google AI Studio | `gemma-4-26b-a4b-it` | `https://generativelanguage.googleapis.com/v1beta/openai` | $0 | Most users — generous limits, zero cost |
| **Free (local, GUI)** | LM Studio | Qwen 3 8B, Llama 3.2, etc. | `http://localhost:1234/v1` | $0 | Privacy-first, no internet required |
| **Free (local, CLI)** | Ollama | Same models | `http://localhost:11434/v1` | $0 | Headless/scripted setups |
| **Budget (cloud)** | OpenAI | `gpt-5-mini` | `https://api.openai.com/v1` | ~$3–5/month | Highest quality output |
| **Flexible (cloud)** | OpenRouter | 300+ models | `https://openrouter.ai/api/v1` | Varies | Model experimentation |

---

## How to Switch Providers

In n8n:

1. Go to **Credentials** → find your **OpenAI API** credential
2. Change the **Base URL** to your provider's endpoint
3. Change the **API Key** to your provider's key
4. Save

Every workflow picks up the change immediately. No restarts needed.

---

## Google AI Studio (Recommended Free Tier)

The best option for most users. Gemma 4 26B produces quality output comparable to GPT-5 mini for scoring and interview prep, at zero cost.

### Setup

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Select or create a Google Cloud project (free, no billing required)
4. Copy the API key

### n8n Configuration

| Field | Value |
|-------|-------|
| API Key | Your Google AI Studio key |
| Base URL | `https://generativelanguage.googleapis.com/v1beta/openai` |

### Model Setting

In your Airtable **Profile** table, set the **AI Model** field to:

```
gemma-4-26b-a4b-it
```

### Rate Limits (as of April 2026)

| Limit | Value |
|-------|-------|
| Requests per minute | 15 |
| Requests per day | 1,500 |
| Tokens per minute | Unlimited |

At 15 RPM, JobSignal processes roughly 7 jobs per minute (each job uses 1 evaluation call + 1 interview prep call for High Fits). The 2-second wait nodes between AI calls keep you well within limits. The daily cap of 1,500 requests is sufficient for evaluating 500+ jobs per day — far more than any typical daily scan produces.

### Required Workflow Adjustments

Gemma 4 (and most open-source models) requires two settings changes in n8n:

**1. Turn OFF "Output Content as JSON"**

In each OpenAI node (Evaluator, Interview Prep, CV Tailor):
- Open the node → scroll to **Options**
- Find **Output Content as JSON** → toggle it **OFF**

The system prompts already enforce JSON output via explicit instructions. The toggle interferes with Gemma 4's output formatting.

**2. Thought tag handling (automatic)**

Gemma 4 sometimes wraps responses in `<thought>` tags despite prompt instructions. The Parse nodes in Workflows 2 and 3 already include stripping logic — they find the first `{` and last `}` to extract clean JSON. No action needed on your part; this is handled automatically.

---

## OpenAI (Budget Tier)

The highest quality output. GPT-5 mini produces the most consistent JSON formatting and the most nuanced scoring reasoning. Costs ~$3–5/month for a typical job search.

### Setup

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add billing — you'll need at least $5 of credit

### n8n Configuration

| Field | Value |
|-------|-------|
| API Key | Your OpenAI key |
| Base URL | `https://api.openai.com/v1` |

### Model Setting

In your Airtable **Profile** table, set the **AI Model** field to:

```
gpt-5-mini
```

### Per-Job Costs

| Action | Token usage | Cost |
|--------|-------------|------|
| Job evaluation | ~2K input / 500 output | ~$0.003 |
| Interview prep (High Fit only) | ~3K input / 2K output | ~$0.007 |
| CV tailoring (High Fit only) | ~3K input / 2K output | ~$0.008 |
| **Total per High Fit job** | | **~$0.02** |

At 30 new jobs/day with 3 High Fits, expect ~$3–5/month.

### No Workflow Adjustments Needed

GPT-5 mini works with the default workflow settings. You can leave "Output Content as JSON" either on or off — both work. The system prompts handle output formatting.

---

## LM Studio (Free Local, GUI)

Run AI inference locally with a graphical interface. Best if you have a GPU (NVIDIA recommended) and want zero cloud dependencies.

### Setup

1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai) (macOS, Windows, Linux)
2. Open the app → go to the **Discover** tab
3. Search for and download a model:
   - **Recommended**: Qwen 3 8B (good balance of quality and speed)
   - **Alternative**: Llama 3.2 8B, Mistral 7B
   - **If you have 16GB+ VRAM**: Qwen 3 14B or larger for better quality
4. Go to the **Local Server** tab
5. Select your downloaded model from the dropdown
6. Click **Start Server**
7. Server runs at `http://localhost:1234/v1`

### n8n Configuration

| Field | Value |
|-------|-------|
| API Key | `lm-studio` (dummy value — local server doesn't validate) |
| Base URL | `http://localhost:1234/v1` |

### Model Setting

In your Airtable **Profile** table, set the **AI Model** field to whatever model you loaded in LM Studio. The exact string doesn't matter for local servers — n8n sends it, but LM Studio uses whatever model is currently loaded regardless.

### Performance Notes

- **GPU inference**: 8B models on a decent GPU (RTX 3060+) process a job evaluation in 5–15 seconds
- **CPU inference**: Works but slow — expect 30–60 seconds per evaluation. Fine for small daily scans (10–20 jobs)
- **Memory**: 8B models need ~6GB VRAM (GPU) or ~8GB RAM (CPU). 14B models need ~10GB VRAM
- **n8n Desktop + LM Studio** is the fully local, $0 stack — no internet needed after model download

### Required Workflow Adjustments

Same as Google AI Studio: turn OFF "Output Content as JSON" in each OpenAI node. The thought tag stripping logic handles any preamble automatically.

---

## Ollama (Free Local, CLI)

Same as LM Studio but command-line based. Better for headless servers or if you prefer terminal workflows.

### Setup

1. Install from [ollama.com](https://ollama.com):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Pull a model:
   ```bash
   ollama pull qwen3:8b
   ```
3. Ollama runs automatically as a background service on `http://localhost:11434`

### n8n Configuration

| Field | Value |
|-------|-------|
| API Key | `ollama` (dummy value) |
| Base URL | `http://localhost:11434/v1` |

### Model Setting

Set the **AI Model** field in your Profile table to match the model you pulled:

```
qwen3:8b
```

### Required Workflow Adjustments

Same as LM Studio and Google AI Studio: turn OFF "Output Content as JSON."

---

## OpenRouter (Flexible Tier)

Access 300+ models through a single API. Useful for experimentation or if you want a specific model not available elsewhere.

### Setup

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to **Keys** → create a new API key
3. Add credits (pay-as-you-go)

### n8n Configuration

| Field | Value |
|-------|-------|
| API Key | Your OpenRouter key |
| Base URL | `https://openrouter.ai/api/v1` |

### Model Setting

Set the **AI Model** field to the OpenRouter model string, e.g.:

```
google/gemma-4-26b-a4b-it
```

Check [openrouter.ai/models](https://openrouter.ai/models) for available models and pricing.

### Important Notes

- **Free tier models exist** but are heavily rate-limited — tested and rejected for JobSignal use. A single job evaluation request can get throttled. Use the paid tier or switch to Google AI Studio for free.
- Pricing varies dramatically by model. Check per-token costs before committing.
- Some models don't support JSON output well. Stick to well-known models (Gemma 4, Llama 3, Claude, GPT) for reliable output.

---

## Choosing the Right Provider

**Start with Google AI Studio** unless you have a specific reason not to. It's free, the rate limits are generous, and Gemma 4 produces quality output. You can always switch later — it's a two-field credential change.

**Switch to OpenAI** if you find Gemma 4's scoring inconsistent or if you want the highest quality interview prep and CV tailoring. The ~$0.02 per High Fit job cost is negligible.

**Go local** if privacy matters, you have a GPU, or you want a completely self-contained system with zero external dependencies. LM Studio is the easiest path; Ollama is better for servers.

---

## Troubleshooting

**AI node returns error "model not found"**
Check that the model string in your Profile table's AI Model field exactly matches what your provider expects. Google AI Studio uses `gemma-4-26b-a4b-it`, not `gemma-4` or `gemma4`.

**Output is wrapped in markdown fences or preamble**
Turn OFF "Output Content as JSON" in the OpenAI node. The Parse nodes handle stripping automatically.

**Rate limit errors with Google AI Studio**
You're likely hitting the 15 RPM limit. The workflows include 2-second wait nodes between calls, but if you have a large batch of new jobs (50+), some calls may hit the limit. The retry logic handles this — jobs will be processed on the next run.

**Local model produces poor quality scores**
Smaller models (7–8B) can struggle with complex scoring rubrics. Try a larger model (14B+) or switch to Google AI Studio / OpenAI for better results. The scoring prompts are optimized for instruction-following models — base models or chat-only finetunes may not produce valid JSON.
