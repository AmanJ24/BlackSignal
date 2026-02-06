# System Architecture

This platform is designed as a **modular dark web intelligence pipeline**.
It does not perform active exploitation or scanning. Instead, it focuses on
passive observation, normalization, enrichment, and risk assessment.

The system enforces three core architectural principles:

1. **Network isolation**
2. **Data immutability**
3. **Explicit orchestration**

---

## Core Principles

### 1. Network Isolation

All network activity targeting the dark web is routed exclusively through
the Tor network. No module performs direct network access.

The `TorManager` is the single authority for:
- SOCKS proxy handling
- circuit isolation
- identity rotation
- failure handling

If Tor connectivity is unavailable, execution halts immediately.

---

### 2. Data Immutability

Each pipeline stage treats its inputs as read-only.

Stages never:
- modify upstream data
- overwrite artifacts
- depend on side effects

Instead, each stage produces a **new artifact** in the next data layer.

This makes the pipeline:
- replayable
- auditable
- safe to partially re-run

---

### 3. Explicit Orchestration

Execution order is not encoded in scripts or directory names.

The pipeline engine:
- resolves dependencies
- schedules independent stages in parallel
- propagates failures deterministically

This prevents hidden coupling and allows the system to grow safely.

---

## Layered Architecture

| Layer | Responsibility |
|------|---------------|
| Collectors | Tor-facing data acquisition |
| Processors | Parsing and normalization |
| Enrichment | External context and validation |
| Analysis | Behavioral and threat reasoning |
| Intelligence | Scoring and aggregation |

Each layer communicates only via structured data artifacts.

---

## Core Components

### Tor Manager
**Path:** `core/tor/tor_manager.py`

- Enforces SOCKS5h usage
- Applies circuit isolation per feature
- Prevents DNS and clearnet leaks
- Fails closed on Tor errors

---

### Pipeline Engine
**Path:** `core/pipeline/pipeline_engine.py`

- Resolves dependency graph
- Executes independent stages concurrently
- Tracks execution state
- Prevents cascading failures

---

### Scoring Engine
**Path:** `core/scoring_engine.py`

- Consumes evidence from multiple features
- Applies weighted confidence scoring
- Produces standardized threat scores

---

This architecture prioritizes correctness, safety, and long-term maintainability
over raw throughput or complexity.

