# Threat Model & Operational Security

This document outlines the risks involved in running this platform
and the mitigations implemented in the architecture.

---

## 1. Deanonymization Risk

**Risk:**  
Correlation of activity across dark web services or linkage to clearnet identity.

**Mitigations:**
- Per-feature Tor circuit isolation
- SOCKS5h to prevent DNS leaks
- No shared sessions across collectors

---

## 2. Network Leakage

**Risk:**  
Traffic escaping to clearnet if Tor fails.

**Mitigations:**
- Centralized Tor Manager
- Fail-closed behavior
- No direct socket or HTTP usage

---

## 3. Malicious Content

**Risk:**  
Exposure to hostile HTML, scripts, or payloads.

**Mitigations:**
- No JavaScript execution
- No headless browsers
- No file execution or sandboxing
- Passive parsing only

---

## 4. API Attribution

**Risk:**  
Linking analyst identity via third-party APIs.

**Mitigations:**
- API keys stored locally
- Environment-based secrets
- Conservative rate limiting

---

## 5. Legal & Ethical Risk

**Risk:**  
Accidental interaction with illegal content.

**Mitigations:**
- Passive observation only
- No exploitation or interaction
- User-defined targets only

---

This platform prioritizes analyst safety over coverage or speed.
