# Pipeline Phases

The pipeline is divided into five strict phases.
Each phase produces artifacts consumed by the next one.

Execution only proceeds forward.

---

## Phase 1: Collection

**Purpose:** Acquire raw data from the dark web and public threat feeds.

Sources include:
- Tor relay consensus
- `.onion` discovery mechanisms
- Dark web marketplaces
- STIX/TAXII feeds

**Output:**  
Unmodified data written to `data/raw/`

---

## Phase 2: Processing

**Purpose:** Convert unstructured content into structured indicators.

This phase extracts:
- IP addresses, domains, wallets
- file hashes
- named entities (actors, groups, locations)

False positives are filtered aggressively.

**Output:**  
Normalized entities written to `data/normalized/`

---

## Phase 3: Enrichment

**Purpose:** Validate and contextualize extracted indicators.

Enrichment sources include:
- reputation databases
- infrastructure intelligence
- geolocation data

This phase does not assign risk. It only adds evidence.

**Output:**  
Evidence-augmented entities written to `data/enriched/`

---

## Phase 4: Analysis

**Purpose:** Infer intent, capability, and structure.

Analysis modules detect:
- behavioral patterns
- reputation signals
- MITRE ATT&CK techniques
- affiliate or RaaS indicators
- handle reuse and correlation

**Output:**  
Intelligence artifacts written to `data/intelligence/`

---

## Phase 5: Scoring & Reporting

**Purpose:** Produce a unified threat assessment.

The scoring engine:
- aggregates all evidence
- applies confidence-weighted logic
- outputs a standardized score

Results are exposed through:
- CLI
- web dashboard

---

Each phase can be re-run independently as long as its inputs exist.

