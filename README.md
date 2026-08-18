# CAGI — Collective AI Governance Interface

A multi-agent deliberation engine implementing **expert-locked persona democracy**: each agent votes, but voting rights are restricted to domain-qualified personas. The system supports four operational modes ranging from synchronous structured debate to real-time SSE streaming.

## Design Rationale

Single-LLM inference suffers from:
1. **Mode collapse**: one model cannot simultaneously hold contradictory expert positions
2. **Authority hallucination**: models generate confident but incorrect claims in specialized domains
3. **No adversarial vetting**: self-correction loops are structurally limited by the same failure mode

CAGI solves this by deploying **multiple expert personas in parallel**, each with a locked cognitive framework, forcing genuine adversarial deliberation before any output is emitted.

## Architecture (v5)

```
Request
  ├── Persona Layer      (system-prompt-locked identity / stance / cognitive framework)
  ├── Memory Layer       (per-expert independent speech history + rebuttal graph)
  └── Synthesis Layer    (consensus analysis + referee adjudication on verbatim positions)
```

### Discussion Pool
All expert utterances are written to a shared pool with **view-limited access** (max 50 entries). Experts do not see raw utterances from other experts; they receive **third-party clerk summaries** that preserve attack relationships and boundary qualifiers while preventing cross-expert plagiarism.

### Four Operational Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Vote** | Synchronous round-robin debate; referee adjudicates on final verbatim positions | Single-question resolution with adversarial stress-testing |
| **Debate** | Multi-round Solvay-style panel with consensus analysis | Deep exploration of a single topic |
| **Free** | Four-phase pipeline: seed → camp reaction → free cross → summary | Open-ended ideation |
| **Stream** | Infinite-round SSE streaming with auto-convergence threshold | Real-time collaborative reasoning |

## Backend Fallback Chain

The engine supports 8 LLM backends with automatic failover:

```
nvidia(253B) → modelscope(Qwen3-235B) → openrouter(free-tier) → glm(flash) → ollama(local)
```

Backend selection is configurable per-request; the fallback chain is traversed until a successful response is obtained.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # configure at least one LLM API key
python main.py         # default port 7788
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | — | Health check + backend status |
| `/personas` | GET | — | List available expert personas |
| `/discuss` | POST | ✅ | Vote-mode deliberation |
| `/solvay/start` | POST | ✅ | Launch Solvay panel debate |
| `/solvay/status/{id}` | GET | — | Query debate status |
| `/solvay/result/{id}` | GET | — | Retrieve final result |
| `/free/start` | POST | ✅ | Launch free-form debate |
| `/stream/start` | POST | ✅ | Launch SSE streaming debate |

## Configuration

All sensitive parameters (API keys, tokens, fallback chains) are read from environment variables. See `.env.example` for the full schema.

## License

MIT
