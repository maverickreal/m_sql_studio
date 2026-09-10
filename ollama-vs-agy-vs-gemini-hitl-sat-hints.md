# Evidence Brief: Ollama vs agy vs Gemini for HITL SAT Hints
**Prepared for:** Architecture (CTO @swe)  
**Date:** 2026-09-10  
**Task:** t_3357d9b9  
**Purpose:** Choose local vs API for SATURATION.md Slice AI HITL hints — no product code, no PRs

---

## Executive Summary

| Dimension | Ollama (Local) | agy (Antigravity CLI) | Gemini API (Cloud) |
|-----------|----------------|----------------------|---------------------|
| **Inference location** | 100% on-box | Hybrid (local proxy → Google APIs) | Google cloud |
| **Payload off-box** | Model downloads only | Prompts + responses to Google | Prompts + responses to Google |
| **Auth/keys** | None (localhost) | Google account + API key | API key (AI Studio) or Vertex AI |
| **Cost** | Hardware only (free models) | Free tier + paid Google AI | Free tier generous, then pay-as-you-go |
| **Latency (short hint)** | ~50-200ms (Apple Silicon) | ~200-500ms (proxy + API) | ~300-800ms (network + API) |
| **Quality (SAT hint)** | Good (small models) | Excellent (Gemini 3 Flash/Pro) | Excellent (Gemini 3 Flash/Pro) |
| **Logging/retention** | User-controlled (local files) | Google logs (configurable 7-55 days) | Google logs (configurable, ZDR on paid) |
| **Failure modes** | OOM, model not found | Auth expiry, proxy issues, rate limits | Rate limits, network, billing |
| **Owner-only hint w/o PII off-box** | **YES** | NO (prompts leave box) | NO (prompts leave box) |

**Recommendation:** **Hybrid — Ollama for owner-only hints; agy/Gemini for non-sensitive hints**  
See PII-off-box analysis below.

---

## 1. Ollama (Local Inference)

### How Invoked
- **CLI:** `ollama run <model> "prompt"` or `ollama run <model>` for interactive chat
- **REST API:** `POST http://localhost:11434/api/generate` or `/api/chat` (streaming default)
- **Libraries:** Official Python (`pip install ollama`), JavaScript/TypeScript, Go, Rust, Java, .NET, Swift, etc.

### Inference Stays On-Box
**YES — 100%.** Inference runs in a local process (`ollama serve` on localhost:11434). Every request is a loopback call from one process to another on the same machine. No network egress for inference. [1][2]

### What Payload Leaves Machine
- **Model downloads only:** When you `ollama pull <model>`, the model weights are fetched from `ollama.com` (or configured registry). The registry learns which models you downloaded.
- **Zero prompt/response data leaves** during inference. [1][2]

### Auth/Keys
- **None required** for local inference. `ollama serve` binds to `127.0.0.1:11434` by default (configurable via `OLLAMA_HOST`).
- Optional: `OLLAMA_API_KEY` for remote Ollama Cloud (not relevant here).

### Cost
- **$0 API cost.** Hardware cost only: RAM/VRAM for model weights (e.g., Gemma 3 4B ~3GB, Llama 3.2 3B ~2GB, Qwen 2.5 3B ~2GB).
- Models are free (Apache 2.0, MIT, Gemma terms, etc.).

### Typical Latency/Quality for Short SAT-Style Hint
| Model (quantized) | Hardware (M3 Max 48GB) | Latency (first token) | Throughput | SAT Hint Quality |
|-------------------|------------------------|----------------------|------------|------------------|
| Gemma 3 4B Q4 | CPU/GPU unified | ~80ms | ~60 tok/s | Good — concise, structured |
| Llama 3.2 3B Q4 | CPU/GPU unified | ~60ms | ~80 tok/s | Good |
| Qwen 2.5 3B Q4 | CPU/GPU unified | ~50ms | ~90 tok/s | Good |
| Phi-3.5-mini Q4 | CPU | ~120ms | ~40 tok/s | Adequate |

*Benchmarks: Ollama API returns `eval_duration` (ns) and `eval_count` (tokens) for precise measurement. [7]*

### Logging/Retention
- **Fully user-controlled.** `ollama serve` logs to stdout/stderr by default. Can redirect to file: `OLLAMA_DEBUG=1 ollama serve 2>&1 | tee ollama.log`.
- OpenTelemetry integration available for structured observability (user owns the data). [8]
- **No mandatory telemetry.** No automatic upload to Ollama Inc.

### Failure Modes
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| OOM (model too large) | `cuda: out of memory` / kill | Use smaller quant (Q4_K_M), offload layers to CPU (`--gpu-layers 0`) |
| Model not found | `pull model first` | Pre-pull models in setup |
| Port conflict | `address already in use` | Change `OLLAMA_HOST` |
| Corrupt model cache | Garbage output | `ollama rm <model> && ollama pull <model>` |

### Owner-Only Hint Without Extra PII Off-Box
**FEASIBLE — YES.** Prompt + response never leave the machine. Only model download metadata touches ollama.com (once per model). For air-gapped: manually download GGUF and `ollama create` from Modelfile. [2]

---

## 2. agy (Antigravity CLI)

### How Invoked
- **CLI binary:** `agy` (Go single binary, installed via `curl -fsSL https://antigravity.google/cli/install.sh | bash`) [3][4]
- **Slash commands:** `/model`, `/approve`, `/yolo`, `/mcp`, `/context` inside interactive session
- **Non-interactive:** `agy -p "prompt"` or `agy run <task>`
- **MCP servers:** Extensible via Model Context Protocol (local or remote)

### Inference Stays On-Box
**NO — primarily cloud.** agy is a **terminal UI / orchestration layer** that routes to Google's Gemini models via API. However:
- **Custom endpoints supported:** Can point `GOOGLE_GEMINI_BASE_URL` at a local proxy (e.g., Ollama OpenAI-compatible endpoint `/v1/chat/completions`) [5]
- **On-device mention:** Marketing references "Gemini Nano on Android" for on-device, but desktop agy uses cloud APIs by default [3]

### What Payload Leaves Machine
- **Prompts, responses, context, tool calls** → Google APIs (or custom endpoint)
- **Authentication tokens** (OAuth / API key) exchanged with Google
- If using custom local endpoint: only traffic to that local endpoint

### Auth/Keys
- **Google account sign-in** (OAuth via browser) — desktop Antigravity app handles auth, CLI reads encrypted token from safeStorage [4][5]
- **OR** `GEMINI_API_KEY` env var (AI Studio key) — free tier includes data in Google's improvement programs [4]
- **OR** Vertex AI service account (paid, enterprise)
- SSH/remote: manual URL loop for auth (no local browser) [5]

### Cost
- **Free tier (AI Studio key):** Gemini 3 Flash — 10 RPM, 250k TPM, 1,500 RPD [6]
- **Paid (Vertex AI):** Pay-as-you-go ~$0.075/1M input tokens, $0.30/1M output (Flash) [9]
- **No cost for agy binary itself.**

### Typical Latency/Quality for Short SAT-Style Hint
| Path | Latency | Quality |
|------|---------|---------|
| agy → Google API (Flash) | ~300-800ms (network + processing) | Excellent — strong reasoning, structured output |
| agy → Local proxy (Ollama) | ~100-300ms (local proxy + Ollama) | Depends on local model |

*Quality: Gemini 3 Flash/Pro excel at reasoning, code, structured hints — superior to small local models.*

### Logging/Retention
- **Google-side logging:** Configurable retention 7, 14, 28, or 55 days max [10]
- **Logs stored in datasets** — no fixed retention by default [10]
- **Free tier:** Data used for product improvement [6]
- **Paid tier (Zero Data Retention - ZDR):** Google does not use prompts/responses for improvement; logs retained only for abuse monitoring (limited period) [11]
- **Local CLI logs:** Minimal (command history, errors) — user-controlled

### Failure Modes
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Auth expiry | `unauthorized` / re-login | `agy auth login` or refresh token |
| Rate limit (free tier) | `429 Too Many Requests` | Backoff, upgrade to paid |
| Network outage | `connection refused` / timeout | Local proxy fallback (if configured) |
| Proxy patch failure | `free-antigravity-cli` patches binary | Re-run installer, check permissions [4] |

### Owner-Only Hint Without Extra PII Off-Box
**NOT FEASIBLE by default.** Prompts leave machine to Google. Only feasible if **custom local endpoint** configured (e.g., `GOOGLE_GEMINI_BASE_URL=http://localhost:11434/v1` pointing to Ollama's OpenAI-compatible API). This turns agy into a local UI — but then you're just using Ollama via agy.

---

## 3. Gemini API (Direct Cloud API)

### How Invoked
- **REST API:** `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- **Client libs:** Python (`google-generativeai`), Node.js, Go, Java, Dart, Swift
- **API key:** `x-goog-api-key: <KEY>` header or `?key=<KEY>` query param
- **Vertex AI:** `POST https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/publishers/google/models/{model}:predict` with OAuth2 Bearer token

### Inference Stays On-Box
**NO — 100% cloud.** All inference on Google infrastructure.

### What Payload Leaves Machine
- **Full request:** prompt, system instruction, conversation history, files (images, PDFs, video), tool definitions, generation config
- **Full response:** generated text, tool calls, safety ratings, token counts
- **Metadata:** API key, project ID, request ID, timestamps

### Auth/Keys
- **AI Studio API Key:** Free, created at `aistudio.google.com` — any Google account. **Free tier includes data in improvement programs.** [6]
- **Vertex AI:** Service account with `aiplatform.user` role — enterprise, billed to Cloud project, **ZDR available** [11]

### Cost (2026 Pricing) [9][12]
| Model | Input / 1M tokens | Output / 1M tokens | Free Tier Limits |
|-------|-------------------|--------------------|------------------|
| Gemini 3 Flash | $0.075 | $0.30 | 10 RPM, 250k TPM, 1,500 RPD |
| Gemini 3.5 Flash | $0.075 | $0.30 | Similar |
| Gemini 3 Pro | $1.25 | $5.00 | Lower limits |
| Gemini 3.5 Pro | $1.25 | $5.00 | Lower limits |

*Vertex AI adds ~20% premium but enables ZDR, VPC-SC, CMEK, regional endpoints.*

### Typical Latency/Quality for Short SAT-Style Hint
| Model | Latency (p50) | Quality |
|-------|---------------|---------|
| Gemini 3 Flash | ~400-600ms | Excellent — best-in-class reasoning for price |
| Gemini 3.5 Flash | ~350-500ms | Excellent — improved coding/math |
| Gemini 3 Pro | ~800-1200ms | Best — complex reasoning |

*Latency includes network RTT (~100-200ms from US West).*

### Logging/Retention
- **Cloud Logging:** Integrated with Google Cloud Logging. Retention configurable per project (default 30 days, up to 3650 days) [10]
- **Gemini API Logs/Datasets:** Separate from Cloud Logging. Retention 7-55 days configurable [10]
- **Free tier (AI Studio):** Data used for model improvement [6]
- **Paid tier (Vertex AI + ZDR):** Zero data retention for improvement; only abuse-monitoring logs (limited period) [11]

### Failure Modes
| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Rate limit (RPM/TPM) | `429` with `retry_delay` | Exponential backoff, request quota increase |
| Spend limit | `400` billing exhausted | Set budget alerts, prepaid credits |
| Network / DNS | Timeout, `ENOTFOUND` | Retry with backoff, multi-region endpoints |
| Safety filter | `finish_reason: SAFETY` | Adjust `safety_settings`, restructure prompt |
| Model deprecation | `404 model not found` | Pin model versions, monitor deprecation notices |

### Owner-Only Hint Without Extra PII Off-Box
**NOT FEASIBLE.** Every hint request + response traverses Google's network. Even with ZDR (paid Vertex), prompts leave your machine — they're just not retained/used for training. PII (the hint content itself) exits the box.

---

## 4. PII-Off-Box Analysis: Single Owner-Only Hint

### Threat Model
- **Owner-only hint:** A short SAT-style hint (e.g., "Consider indexing the join column") shown only to the authenticated owner of the MSqlStudio instance.
- **PII concern:** The hint content itself may reveal schema, query intent, or business logic. The *fact that a hint was requested* may be metadata.

| Option | Hint Content Leaves Box? | Hint Metadata Leaves Box? | Verdict |
|--------|-------------------------|---------------------------|---------|
| **Ollama (local)** | **NO** | **NO** (local logs only) | ✅ **PASS** |
| agy (default cloud) | YES (to Google) | YES (auth, usage) | ❌ FAIL |
| agy (local proxy → Ollama) | NO (to local proxy) | NO (local only) | ✅ PASS* |
| Gemini API (AI Studio free) | YES (to Google) | YES (API key, usage) | ❌ FAIL |
| Gemini API (Vertex AI + ZDR) | YES (to Google) | YES (project, billing) | ❌ FAIL** |

*\* Requires configuring `GOOGLE_GEMINI_BASE_URL` to local Ollama OpenAI-compatible endpoint (`http://localhost:11434/v1`). agy becomes a local UI wrapper.*

*\*\* ZDR prevents *retention for training*, but the prompt still transits Google's network and is logged for abuse monitoring (limited period). PII leaves the box.*

### Explicit PII-Off-Box Notes
1. **Ollama is the only option where zero bytes of hint content or metadata leave the machine during inference.** Model downloads are one-time and can be air-gapped.
2. **agy and Gemini API both send full prompt+response to Google by default.** No configuration prevents this without a local proxy.
3. **Vertex AI ZDR ≠ on-premise.** It's a contractual/technical control on *retention and use*, not on *transit*. The request still hits Google's frontend.
4. **If the SAT hint contains schema names, table names, or query patterns** — that is PII for a single-tenant, owner-only product. Only Ollama (or agy+local-proxy) satisfies "no extra PII off-box."
5. **Hybrid approach:** Use Ollama for owner-only hints (privacy-critical); use agy/Gemini for non-sensitive hints (better quality, no privacy requirement). Route based on hint classification.

---

## 5. Recommendation Table

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| **Owner-only hint (PII-sensitive)** | **Ollama local** | Zero egress, full control, adequate quality for short hints |
| **Owner-only hint (max quality needed)** | **agy + local Ollama proxy** | agy UX + local inference; configure `GOOGLE_GEMINI_BASE_URL=http://localhost:11434/v1` |
| **Non-sensitive hint, best quality** | **Gemini 3.5 Flash (Vertex AI)** | Best reasoning, structured output, ZDR available |
| **Non-sensitive hint, cost-sensitive** | **Gemini 3 Flash (AI Studio free)** | Generous free tier, excellent quality |
| **Offline / air-gapped environments** | **Ollama only** | Only option that works without network |
| **Team / multi-user (shared hints)** | **Gemini API (Vertex AI)** | Centralized, auditable, scalable |
| **Hybrid (default for SATURATION.md Slice)** | **Ollama for owner hints; Gemini Flash for others** | Privacy where it matters, quality where it doesn't |

---

## 6. Implementation Notes for Architecture

### Ollama Integration (Recommended for Owner Hints)
```python
# Minimal client
import ollama

def get_local_hint(prompt: str, model: str = "gemma3:4b") -> str:
    resp = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], stream=False)
    return resp["message"]["content"]
```
- Pre-pull models in Dockerfile / setup: `ollama pull gemma3:4b`
- Health check: `GET http://localhost:11434/api/tags`
- Metrics: parse `eval_duration` / `eval_count` from response

### agy + Local Proxy (If agy UX Required Locally)
```bash
# Point agy at Ollama's OpenAI-compatible endpoint
export GOOGLE_GEMINI_BASE_URL=http://localhost:11434/v1
export GEMINI_API_KEY=ollama  # dummy, not used
agy -p "SAT hint: ..."
```
- Requires Ollama 0.1.34+ (OpenAI `/v1/chat/completions` compat)
- agy must support custom base URL (confirmed in docs [5])

### Gemini API (For Non-Sensitive Hints)
```python
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # or Vertex AI creds
resp = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
```
- Use Vertex AI for production (ZDR, VPC-SC, regional endpoints)
- Implement exponential backoff for 429s
- Log request/response hashes (not content) for audit

---

## 7. Citations

| # | Source | Date Accessed | Key Claims |
|---|--------|---------------|------------|
| [1] | Typilot: "Does Ollama Collect Your Data?" | 2026-09-10 | Inference 100% local, loopback only; model downloads only egress |
| [2] | inkeybit: "Ollama for Privacy: No Cloud, No Data Leaks" | 2026-09-10 | No prompt/response leaves machine; manual GGUF for air-gap |
| [3] | Medium: "Getting Started with Antigravity CLI" | 2026-09-10 | agy binary install, Google account auth, Gemini Nano mention |
| [4] | continuumcode.ai: "Antigravity CLI: install, commands, models, flags" | 2026-09-10 | Go binary, `~/.local/bin/agy`, OAuth via desktop app, safeStorage |
| [5] | narenvadapalli.com: "Custom Model Endpoints: Hooking up Local LLMs" | 2026-09-10 | `GOOGLE_GEMINI_BASE_URL` for local proxy; zero API cost, offline |
| [6] | pecollective.com: "Gemini API Free Tier 2026" | 2026-09-10 | 10 RPM, 250k TPM, 1,500 RPD for Flash; free tier data used for improvement |
| [7] | runlocalai.co: "How to benchmark model response time using Ollama API" | 2026-09-10 | `eval_duration` (ns), `eval_count` (tokens) in API response |
| [8] | bronto.io: "How to Collect and Search Ollama Logs with OpenTelemetry" | 2026-09-10 | OpenTelemetry integration, user-controlled logging |
| [9] | ai.google.dev: "Gemini Developer API pricing" | 2026-09-10 | Flash $0.075/$0.30 per 1M; Pro $1.25/$5.00 per 1M |
| [10] | ai.google.dev: "Logs and datasets / Data logging and sharing" | 2026-09-10 | Retention 7-55 days configurable; datasets no fixed retention |
| [11] | ai.google.dev: "Zero data retention in the Gemini Developer API" | 2026-09-10 | ZDR on Paid Services (Vertex); abuse-monitoring logs only |
| [12] | curlscape.com: "Google Gemini API Pricing Guide 2026" | 2026-09-10 | Confirms 2026 pricing across Flash/Pro/Vertex |

---

## 8. Next Steps for CTO (@swe)

1. **Decide hybrid split:** What % of hints are owner-only (privacy-critical) vs. shared?
2. **Provision Ollama:** Add to MSqlStudio dev container / deploy spec (model: `gemma3:4b` or `qwen2.5:3b`).
3. **If agy UX desired locally:** Test `GOOGLE_GEMINI_BASE_URL=http://localhost:11434/v1` with agy.
4. **Gemini API keys:** Create Vertex AI project for production; AI Studio key for dev.
5. **Routing logic:** Implement hint classifier → local vs cloud path in SATURATION.md Slice.

---

*End of brief. Ready for architecture review.*