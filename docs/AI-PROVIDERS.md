# AI Providers Guide

> 🚧 **Coming soon** — Detailed configuration for each AI provider tier.

## Quick Reference

| Tier | Provider | Base URL | Model |
|------|----------|----------|-------|
| **Free (cloud)** | Google AI Studio | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemma-4-26b-a4b-it` |
| **Free (local)** | LM Studio | `http://localhost:1234/v1` | Any downloaded model |
| **Free (local)** | Ollama | `http://localhost:11434/v1` | Any pulled model |
| **Budget** | OpenAI | `https://api.openai.com/v1` | `gpt-5-mini` |
| **Flexible** | OpenRouter | `https://openrouter.ai/api/v1` | 300+ models |

## How to Switch

In n8n: **Credentials → OpenAI API → set Base URL and API Key.** Every workflow inherits it automatically.

## Google AI Studio Notes

- Turn **off** "Output Content as JSON" toggle in each AI node
- Free tier: 15 RPM, 1,500 RPD (as of April 2026)
- Get your free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
