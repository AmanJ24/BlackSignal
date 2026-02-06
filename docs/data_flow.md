# Data Flow & Schema Contracts

The platform enforces strict data contracts between stages.
No stage assumes how its input was generated.

---

## Data Layers

### `data/raw/`
- Direct output of collectors
- May include HTML or loosely structured JSON
- Never modified after creation

---

### `data/normalized/`
- Structured entities with stable identifiers
- No external context
- No scoring or assumptions

---

### `data/enriched/`
- Normalized entities with appended evidence
- Evidence is additive only

---

### `data/intelligence/`
- High-level analytical artifacts
- Ready for scoring and presentation

---

## Evidence Model

All enrichment and analysis modules emit **Evidence Objects**.

Evidence objects are the only input to the scoring engine.

```json
{
  "type": "string",
  "description": "string",
  "confidence": 0.0,
  "source_feature": "string"
}

