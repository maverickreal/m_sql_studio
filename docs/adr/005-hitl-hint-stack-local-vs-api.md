# ADR 005: HITL Hint Stack — Local vs API, Say Consent, PII Boundary

**Status:** Accepted
**Date:** 2026-09-10
**Deciders:** Architect (this ADR), CTO @swe (handoff)
**Tags:** hitl, sat, hints, privacy, ollama, gemini, hybrid

---

## Context

SATURATION.md Slice AI requires a Human-in-the-Loop (HITL) hint stack that shows SAT-style hints to the **owner only** on **failed submit** events. The hint content may contain schema names, query patterns, or business logic — constituting PII for a single-tenant, owner-only product.

The recon brief (`ollama-vs-agy-vs-gemini-hitl-sat-hints.md`) compared three options:

| Option | Inference Location | Hint Content Off-Box? | Owner-Only Feasible? |
|--------|-------------------|----------------------|---------------------|
| **Ollama (local)** | 100% on-box | **NO** | ✅ YES |
| agy (default) | Google cloud | YES (to Google) | ❌ NO |
| agy + local proxy | On-box (via Ollama) | NO (to local proxy) | ✅ YES* |
| Gemini API (AI Studio) | Google cloud | YES (to Google) | ❌ NO |
| Gemini API (Vertex + ZDR) | Google cloud | YES (transit) | ❌ NO** |

*ZDR prevents retention for training, but prompt still transits Google's network and is logged for abuse monitoring. PII leaves the box.

**Key finding:** **Ollama is the only option where zero bytes of hint content or metadata leave the machine during inference.**

---

## Decision

### 1. Architecture: Hybrid — Ollama for Owner Hints; Gemini Flash for Non-Sensitive Hints

- **Owner-only hints (privacy-critical):** Ollama local inference only. Model: `gemma3:4b` (or `qwen2.5:3b` as fallback). Runs in-container via `ollama serve` on `localhost:11434`.
- **Non-sensitive hints (shared, team, public):** Gemini 3.5 Flash via Vertex AI (production) or AI Studio key (dev). Best quality, no privacy requirement.

**Routing rule:** The hint classifier in the SATURATION.md Slice routes each hint request to the appropriate backend based on `hint.classification ∈ {owner_only, shared}`.

### 2. Say Consent Gate — No Extra PII Off-Box Without Owner Say

- **Default:** Zero PII leaves the box. Ollama runs fully local; no network egress for inference.
- **Explicit opt-in (`say`):** Owner must explicitly consent (via settings UI or CLI flag) before ANY hint request is routed to a cloud backend (Gemini).
- **Scope of `say`:** Consent is per-hint-classification. `say=true` for `shared` hints only. `owner_only` hints **never** leave the box, regardless of `say`.
- **Revocation:** Owner can revoke `say` at any time; subsequent shared hints fall back to local Ollama (degraded quality) or are suppressed.

### 3. Sequence: Failed Submit → Say Check → One Owner-Only Hint

```
User submits SAT task
        │
        ▼
┌───────────────────┐
│ Submit FAILED?    │──No──▶ No hint shown (success path)
└─────────┬─────────┘
          │ Yes
          ▼
┌───────────────────┐
│ Classify hint     │──shared──▶ Check `say` consent
│ (owner_only vs    │            │
│  shared)          │            ▼
└─────────┬─────────┘   ┌───────────────┐
          │             │ say = true?   │──No──▶ Suppress / local fallback
          │ owner_only  └───────┬───────┘
          ▼                     │ Yes
┌───────────────────┐           ▼
│ Route to OLLAMA   │    ┌───────────────┐
│ (local, no egress)│    │ Call Gemini   │
└─────────┬─────────┘    │ (cloud, PII    │
          │              │  leaves box)   │
          ▼              └───────┬────────┘
┌───────────────────┐            │
│ Render ONE hint   │◀───────────┘
│ to OWNER only     │
│ (no stack, no     │
│  broadcast)       │
└───────────────────┘
```

**Constraints encoded:**
- Exactly **one** hint per failed submit (not on success, not stacked, not broadcast to others).
- Hint is **owner-only** — authenticated session check required before render.
- No hint on successful submit.

### 4. PII Boundary: What Leaves the Box vs Stays Local

| Data | Owner-Only Hint (Ollama) | Shared Hint (Gemini, with `say`) |
|------|-------------------------|----------------------------------|
| Hint prompt (schema, query, context) | **Stays local** (loopback only) | Leaves box → Google API |
| Hint response (generated text) | **Stays local** | Leaves box → Google API |
| Model weights | Downloaded once (opt-in, can air-gap) | N/A (cloud) |
| Auth tokens / API keys | None | `GEMINI_API_KEY` or Vertex SA (stored in secrets manager) |
| Request metadata (timing, model, classification) | Local logs only (user-controlled) | Google Cloud Logging (configurable retention) |
| `say` consent flag | Local config only | Sent with request (required for audit) |

**Who can see the hint:**
- Owner-only: Only the authenticated owner of the MSqlStudio instance (session-scoped).
- Shared: Per product sharing model (team, org, public) — defined elsewhere.

**Where the model runs:**
- Owner-only: `ollama serve` on `localhost:11434` (in-container, same pod/VM).
- Shared: Google Vertex AI (regional endpoint, e.g., `us-central1`) or AI Studio global endpoint.

### 5. Fallback If Model Is Down

| Backend | Failure Mode | Fallback Behavior |
|---------|--------------|-------------------|
| **Ollama** | OOM, port conflict, model not found, corrupt cache | 1. Retry with smaller quant (Q4→Q3) / CPU offload<br>2. If persistent: suppress hint, log degradation event, continue SAT flow without hint |
| **Gemini** | Rate limit (429), spend limit, network/DNS, safety filter, model deprecation | 1. Exponential backoff (max 3 retries)<br>2. On persistent failure: route to Ollama (local fallback, degraded quality)<br>3. If Ollama also down: suppress hint, log degradation event |

**Degradation events** are emitted to local audit log (structured JSON) for observability — never sent off-box without `say`.

### 6. Interfaces / Patterns for Implementer (No Extra Scope)

#### 6.1 HintProvider Interface (Strategy Pattern)
```typescript
// packages/sat-hints/src/hint-provider.ts
export interface HintProvider {
  readonly classification: 'owner_only' | 'shared';
  readonly name: string;
  
  generateHint(prompt: HintPrompt): Promise<HintResult>;
  healthCheck(): Promise<HealthStatus>;
  getModelInfo(): ModelInfo;
}

export interface HintPrompt {
  taskId: string;
  userQuery: string;
  schemaContext: SchemaSummary;
  failureReason: string;
  attemptNumber: number;
}

export interface HintResult {
  text: string;
  model: string;
  latencyMs: number;
  tokensIn: number;
  tokensOut: number;
}
```

#### 6.2 Concrete Providers
- `OllamaHintProvider` — implements `HintProvider` for `owner_only`. Uses `ollama` npm package. Pre-pulls `gemma3:4b` in Dockerfile.
- `GeminiHintProvider` — implements `HintProvider` for `shared`. Uses `@google/generative-ai` or Vertex AI client. Requires `GEMINI_API_KEY` secret.

#### 6.3 Router / Classifier
```typescript
// packages/sat-hints/src/hint-router.ts
export class HintRouter {
  constructor(
    private readonly ollama: OllamaHintProvider,
    private readonly gemini: GeminiHintProvider,
    private readonly consentStore: ConsentStore,
    private readonly auditLog: AuditLogger
  ) {}

  async getHint(prompt: HintPrompt): Promise<HintResult | null> {
    const classification = this.classify(prompt);
    
    if (classification === 'owner_only') {
      return this.executeWithFallback(this.ollama, prompt, 'owner_only');
    }
    
    // shared hint — check say consent
    const say = await this.consentStore.getSayConsent();
    if (!say) {
      this.auditLog.emit({ type: 'hint_suppressed', reason: 'no_say_consent', classification });
      return this.executeWithFallback(this.ollama, prompt, 'shared_fallback_local');
    }
    
    return this.executeWithFallback(this.gemini, prompt, 'shared');
  }

  private async executeWithFallback(
    primary: HintProvider,
    prompt: HintPrompt,
    route: string
  ): Promise<HintResult | null> {
    try {
      const result = await primary.generateHint(prompt);
      this.auditLog.emit({ type: 'hint_generated', route, model: primary.name });
      return result;
    } catch (err) {
      this.auditLog.emit({ type: 'hint_fallback', route, error: err.message });
      // Fallback logic per Section 5
      if (primary instanceof OllamaHintProvider) return null; // suppress
      return this.ollama.generateHint(prompt); // Gemini → Ollama fallback
    }
  }
}
```

#### 6.4 Consent Store (Say Gate)
```typescript
// packages/sat-hints/src/consent-store.ts
export interface ConsentStore {
  getSayConsent(): Promise<boolean>;
  setSayConsent(enabled: boolean): Promise<void>;
  // Backed by local config file / SQLite — no cloud sync
}
```

#### 6.5 Audit Logger (Local Only)
```typescript
// packages/sat-hints/src/audit-logger.ts
export interface AuditLogger {
  emit(event: AuditEvent): void;
  // Writes structured JSONL to local file (rotated daily)
  // Never transmits off-box
}
```

#### 6.6 Wiring (DI Container)
```typescript
// packages/sat-hints/src/index.ts
export function createHintStack(config: HintStackConfig): HintRouter {
  const ollama = new OllamaHintProvider({
    host: config.ollamaHost || 'http://localhost:11434',
    model: config.ollamaModel || 'gemma3:4b',
  });
  
  const gemini = config.geminiApiKey 
    ? new GeminiHintProvider({ apiKey: config.geminiApiKey, model: 'gemini-3.5-flash' })
    : null;
  
  const consent = new FileConsentStore(config.consentPath);
  const audit = new FileAuditLogger(config.auditLogPath);
  
  return new HintRouter(ollama, gemini, consent, audit);
}
```

---

## Consequences

### Positive
- **Zero PII off-box for owner hints** — satisfies hard privacy requirement.
- **Hybrid quality/cost** — best cloud model for shared hints; free local for owner hints.
- **Graceful degradation** — SAT flow never blocks on hint generation.
- **Testable boundaries** — `HintProvider` interface enables unit testing with fakes.
- **No vendor lock-in for owner hints** — Ollama models are portable GGUF.

### Negative / Risks
- **Local model quality ceiling** — Gemma 3 4B is "good" but not "excellent" for complex SAT hints. Mitigation: prompt engineering, few-shot examples baked into prompt template.
- **Operational burden** — Ollama must be running in-container. Mitigation: health check + pre-pull in Dockerfile; systemd/container restart policy.
- **Two model surfaces to maintain** — prompt templates differ. Mitigation: shared prompt builder with classification-specific sections.

### Neutral
- **Say consent adds UX step** — owner must enable shared hints explicitly. This is intentional (privacy-by-design).

---

## Engineering Done-List (Finite, Handoff to Implementer)

- [ ] Add `ollama` to MSqlStudio dev container / Dockerfile; pre-pull `gemma3:4b`
- [ ] Implement `HintProvider` interface + `OllamaHintProvider` + `GeminiHintProvider`
- [ ] Implement `HintRouter` with classification + say-gate + fallback logic
- [ ] Implement `ConsentStore` (local file/SQLite) + `AuditLogger` (local JSONL)
- [ ] Wire DI in SATURATION.md Slice entry point
- [ ] Add health endpoint: `GET /api/sat/hints/health` → returns `{ ollama: 'up'|'down', gemini: 'up'|'down'|'unconfigured' }`
- [ ] Unit tests: router classification, say-gate, fallback chain, consent revocation
- [ ] Integration test: failed submit → owner-only hint rendered once (playwright)
- [ ] Document `say` consent CLI flag + settings UI toggle (separate spec)

---

## Handoff to CTO (@swe)

This ADR is **architecture-only**. No product code written. The done-list above is the complete implementation scope for the engineer. 

**Decisions requiring CTO confirmation before engineer starts:**
1. Confirm hybrid split (owner-only = Ollama, shared = Gemini Flash) — or pure local?
2. Confirm `gemma3:4b` as default owner-hint model (vs `qwen2.5:3b` for lower RAM).
3. Confirm Vertex AI vs AI Studio for shared hints (Vertex = ZDR, regional, billed; AI Studio = free tier, data used for improvement).

**File location:** `msql-studio/docs/adr/005-hitl-hint-stack-local-vs-api.md`