# EVIDA — Hackathon Submission Assets & Demonstration Screenshots

This document specifies the exact submission assets, critical screens, and descriptions prepared for the **Nebius × NVIDIA Global AI Hackathon**.

---

## 1. Submission Identity & Positioning

- **Project Name:** EVIDA — Evidence-Driven AI Software Repair
- **One-Line Description:**
  > **AI proposes software repairs. EVIDA deterministically verifies whether they actually work.**
- **Short Description (Summary):**
  > EVIDA is an evidence-driven AI software repair system. It uses NVIDIA Nemotron through Nebius Token Factory to investigate software failures and propose regression tests and patches, then independently executes and verifies those changes in a sandbox. A repair is marked VERIFIED only when the regression passes, the baseline suite passes, and source integrity is preserved. Every investigation produces a cryptographically hashed evidence bundle.
- **Primary Category:** Autonomous Software Engineering & Developer Tools
- **Core Maxim:** *AI proposes. Evidence decides.*

---

## 2. Five Critical Demo Screenshots

The following five screens communicate the complete technical value proposition of EVIDA:

### Screenshot 1 — Failure Reproduction
- **URL / Location:** `http://localhost:3000/investigations/{id}` → **Failure Reproduction Panel**
- **Elements Captured:**
  - Status Badge: `REPRODUCED` (Rose tag)
  - Reproduction Command: `pytest tests/test_bug.py`
  - Exit Code: `1`
  - Execution Duration: `142 ms`
  - Stdout Terminal:
    ```text
    ============================= test session starts ==============================
    FAILED tests/test_bug.py::test_divide_bug - assert 20 == 5
    ============================== 1 failed in 0.14s ===============================
    ```
- **Narrative:** Deterministic sandbox ground truth established before invoking any AI model.

---

### Screenshot 2 — AI Root Cause Investigation (NVIDIA Nemotron)
- **URL / Location:** `http://localhost:3000/investigations/{id}` → **AI Investigation Panel**
- **Elements Captured:**
  - Status Tag: `INVESTIGATING` (Purple badge)
  - Provenance Banner: `AI PROPOSAL (UNTRUSTED OUTPUT)` (Amber badge)
  - AI Provider Tag: `Nebius Token Factory`
  - Model Identifier: `nvidia/Nemotron-3_5-Lightning`
  - Confidence Score: `99%`
  - Hypothesis: *"The divide function in src/calculator.py multiplies its operands instead of dividing them."*
  - Root Cause Candidate: `src/calculator.py`, symbol `divide`, line 2 (`return a * b`).
- **Narrative:** NVIDIA Nemotron causal diagnosis strictly labeled as an untrusted proposal.

---

### Screenshot 3 — Regression Test Synthesis & Deterministic Proof
- **URL / Location:** `http://localhost:3000/investigations/{id}` → **Regression Test Section**
- **Elements Captured:**
  - Left Panel: **AI Proposed Regression Test** (Synthesized `test_divide_regression`)
  - Right Panel: **Deterministic Verification Evidence**
  - Verification Verdict: `REGRESSION_PROVEN` (Emerald badge)
  - Exit Code: `1` (`ASSERTION_FAILURE`)
  - Stdout Terminal: `FAILED tests/test_regression.py::test_divide_regression - assert 20 == 5`
- **Narrative:** Synthesized regression test is deterministically proven against the original unpatched codebase.

---

### Screenshot 4 — Final Deterministic Verification (Double Validation)
- **URL / Location:** `http://localhost:3000/investigations/{id}` → **Phase 6 Verification Grid**
- **Elements Captured:**
  - Master Verification Header: `STATUS: VERIFIED`
  - Emerald Banner: *Double Validation Rule Satisfied: VERIFIED*
  - 3-Step Verification Grid:
    1. **Patch Application:** `Exit Code 0`, `src/calculator.py` modified in fresh ephemeral workspace.
    2. **Original Regression:** `Before: FAIL` → `After: PASS` (`Exit Code 0`).
    3. **Existing Test Suite:** `PASS` (`pytest` exited with code 0).
  - Source Integrity Bar: `Cryptographic Source Integrity: The original repository artifact remained unchanged (Pre == Post SHA-256 matched).`
- **Narrative:** Pure deterministic verification proof without LLM self-evaluation.

---

### Screenshot 5 — Cryptographic Evidence Bundle & Provenance
- **URL / Location:** `http://localhost:3000/investigations/{id}` → **Phase 7 Evidence Bundle Section**
- **Elements Captured:**
  - Header: `Phase 7 — Evidence Bundle, Provenance & Audit System`
  - Global Bundle Hash: `bundle_sha256: b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9`
  - Export Button: `Export Bundle (.json)`
  - Provenance Taxonomy Legend:
    - `AI_PROPOSAL` (Purple)
    - `DETERMINISTIC_EXECUTION` (Blue)
    - `CRYPTOGRAPHIC_INTEGRITY` (Emerald)
    - `SYSTEM_METADATA` (Slate)
    - `AUDIT_EVENT` (Amber)
  - Chronological Evidence Timeline: 11+ aggregated evidence items with individual content SHA-256 digests.
- **Narrative:** Immutable, tamper-evident audit record suitable for high-assurance review.

---

## 3. Secondary Failure Demonstration Screen (Safety Invariant)

- **Scenario:** Incomplete or flawed patch synthesized (e.g. replacing `*` with `-`).
- **Elements Captured:**
  - Status Tag: `UNVERIFIED` (Rose badge)
  - Failure Banner:
    > **Double Validation Rule Failed: UNVERIFIED**  
    > *The proposed patch was not verified because deterministic regression validation failed.*
  - Reason Classification: `REGRESSION_STILL_FAILING`
- **Narrative:** Demonstrates that EVIDA refuses to mark a patch verified simply because an AI generated it.

---

## 4. Video Demonstration & Recording Guide

- **Demo Script:** [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
- **Duration:** Exactly 2 minutes 50 seconds (under the 3:00 minute limit).
- **Format:** 1080p 60 FPS recording with screen capture and voiceover.
- **Demo Fixture:** `tests/fixtures/broken_python_repo.zip`

