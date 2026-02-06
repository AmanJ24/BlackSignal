# Contributor Guide

This project prioritizes correctness, safety, and architectural clarity.
Contributions are welcome, but must follow the rules below.

Breaking these rules will result in rejection.

---

## 1. Networking Rules

All network access **must** go through the Tor Manager.

Direct use of networking libraries is forbidden.

❌ Not allowed:
- requests.get()
- urllib
- curl
- aiohttp without TorManager

✅ Required:
```python
from core.tor.tor_manager import TorManager

tm = TorManager(...)
session = tm.session(purpose="feature_name")
session.get(url)
```

This rule exists to prevent deanonymization and traffic leaks.

---

## 2. Data Integrity Rules

Pipeline stages must treat inputs as read-only.

### Rules:

- never modify files in previous data layers

- never overwrite artifacts

- always write new outputs

Data flows strictly:
raw → normalized → enriched → intelligence

---

## 3. Execution Order

Features must not assume:

- pipeline order

- presence of other stages

- availability of external data

Execution order is controlled by the pipeline engine only.

---

## 4. Analysis Contributions

Analysis modules must:

- emit evidence, not final scores

- include confidence values (0.0–1.0)

- explain signals in plain language

The scoring engine is the only component allowed to calculate threat scores.

---

## When in Doubt

If a change affects:

- networking

- data schemas

- execution order

Open an issue before implementing it.
