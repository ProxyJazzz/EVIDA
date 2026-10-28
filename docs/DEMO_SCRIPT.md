# EVIDA — 3-Minute Video Demo & Presentation Script

> **Video Duration Limit:** ≤ 3:00 minutes  
> **Maxim:** *AI proposes. Evidence decides.*  
> **Core Concept:** Proving software repair through deterministic sandbox evidence rather than trusting LLM self-evaluation.

---

## Storyboard & Timing Breakdown

```text
[ 0:00 - 0:20 ] Problem: The AI Patch Trust Crisis
[ 0:20 - 0:40 ] Phase 2: Failure Reproduction in Sandbox
[ 0:40 - 1:00 ] Phase 3: AI Investigation with NVIDIA Nemotron
[ 1:00 - 1:20 ] Phase 4: Regression Test Synthesis & Deterministic Proof
[ 1:20 - 1:40 ] Phase 5: Candidate Patch Synthesis & Structural Safety
[ 1:40 - 2:10 ] Phase 6: Deterministic Double Validation (The Differentiator)
[ 2:10 - 2:40 ] Phase 7: Cryptographic Evidence Bundle & Provenance Chain
[ 2:40 - 3:00 ] Conclusion: High-Assurance AI Software Engineering
```

---

## Detailed Transcript & Visual Cue Guide

### 0:00 – 0:20 | The Problem
- **Visual:** Open IDE showing a broken Python repository (`divide(10, 2)` returning `20` because multiplication `*` was written instead of division `/`). Transition to a traditional AI chat assistant claiming *"I have fixed your bug!"* with no verification.
- **Voiceover:**
  > "Today's AI coding assistants are incredible at writing code that *looks* right. But looking right isn't proof. When an AI proposes a bug fix, how do you know it actually works? How do you know it didn't break existing tests? And why should a software engineer trust an AI's self-confidence score?
  >
  > Welcome to **EVIDA: Evidence-Driven AI Software Repair**. Our maxim: **AI proposes. Evidence decides.**"

---

### 0:20 – 0:40 | Deterministic Failure Reproduction
- **Visual:** Open EVIDA Web Dashboard. Drag-and-drop `broken_python_repo.zip`. The UI transitions to `INGESTING`, computes the archive SHA-256 digest, and triggers reproduction. The live terminal displays `pytest tests/test_bug.py` running in an isolated sandbox and exiting with code 1.
- **Voiceover:**
  > "EVIDA starts by treating the bug report as an unproven claim. We ingest the repository archive, compute its cryptographic hash, and spin up an isolated ephemeral sandbox.
  >
  > Running `pytest tests/test_bug.py` yields exit code 1: defect reproduced. Notice: no AI has been called yet. We establish deterministic ground truth first."

---

### 0:40 – 1:00 | AI Investigation via Nebius & NVIDIA Nemotron
- **Visual:** Click **Investigate**. EVIDA extracts relevant file context, stack traces, and sends a bounded prompt to **Nebius Token Factory** running **NVIDIA Nemotron-3_5-Lightning**. The UI renders the AI Investigation Card with confidence 0.99 and root cause: `src/calculator.py line 2 in divide()`.
- **Voiceover:**
  > "Now we bring in AI reasoning. Powered by **NVIDIA Nemotron through Nebius Token Factory**, EVIDA analyzes the failure trace and hypothesizes the root cause: multiplication instead of division.
  >
  > But notice the amber badge in the UI: **AI PROPOSAL (UNTRUSTED)**. EVIDA never treats AI hypotheses as truth. We require proof."

---

### 1:00 – 1:20 | Regression Test Synthesis & Proof
- **Visual:** EVIDA automatically requests a standalone regression test from the NVIDIA model (`test_divide_regression`). The AST validator verifies safety, and the test is executed against the **original, unpatched** codebase. The terminal shows assertion failure: `assert 20 == 5`. The badge flips to `REGRESSION_PROVEN`.
- **Voiceover:**
  > "Next, NVIDIA Nemotron synthesizes a regression test specifically designed to fail on the bug. EVIDA validates the AST to block malicious calls, extracts a fresh unpatched workspace, and runs it.
  >
  > The test fails with exit code 1. The regression is now deterministically proven on the original source code."

---

### 1:20 – 1:40 | Candidate Patch Synthesis & Structural Validation
- **Visual:** EVIDA synthesizes a unified diff patch replacing `return a * b` with `return a / b`. The unified diff viewer renders line-by-line syntax highlighting. A prominent banner displays: `STATUS: VALIDATED — NOT VERIFIED`.
- **Voiceover:**
  > "Using the proven regression evidence, NVIDIA Nemotron generates a candidate patch. EVIDA validates that the patch touches only authorized files, doesn't touch test files, and contains zero security violations.
  >
  > But even a valid patch is **NOT VERIFIED**. A valid patch is just a proposal."

---

### 1:40 – 2:10 | Deterministic Double Validation (The Differentiator)
- **Visual:** Click **Verify Patch**. The live execution grid lights up:
  1. Ephemeral Sandbox Created.
  2. Candidate Patch Applied (`Exit Code: 0`).
  3. Validation 1: Proven Regression Test Executed (`Exit Code: 0, PASS`).
  4. Validation 2: Existing Baseline Test Suite Executed (`Exit Code: 0, PASS`).
  5. Cryptographic Source Integrity Verified (`SHA-256 Before == After`).
  6. The header flashes emerald: `VERDICT: VERIFIED`.
- **Voiceover:**
  > "Here is where EVIDA stands alone. In an isolated ephemeral sandbox, EVIDA applies the candidate patch and executes **Double Validation**:
  >
  > First: Does the proven regression test pass now? **Yes, exit code 0.**
  > Second: Did the patch break any existing tests in the baseline suite? **No, all baseline tests pass.**
  > Third: Did the original repository artifact remain untouched? **Yes, SHA-256 matches exactly.**
  >
  > Only now does the verdict become **VERIFIED**. Zero human guesswork. Zero AI discretion. 100% deterministic execution evidence."

---

### 2:10 – 2:40 | Cryptographic Evidence Bundle
- **Visual:** Scroll down to the **Phase 7 Evidence Bundle Card**. Show the Provenance Taxonomy (`AI_PROPOSAL` vs `DETERMINISTIC_EXECUTION` vs `CRYPTOGRAPHIC_INTEGRITY`). Click **Export Bundle (.json)** and open the formatted JSON file in an editor showing `bundle_sha256` and the tamper-evident audit trail.
- **Voiceover:**
  > "Finally, EVIDA compiles everything into the **EVIDA Evidence Bundle**.
  >
  > Every hypothesis, diff, exit code, duration, and cryptographic hash is assembled into an immutable, append-only record bound by a global SHA-256 hash.
  >
  > If a single line of output or timestamp is altered, the cryptographic digest changes immediately. Reviewers don't have to trust our word—they have mathematical proof."

---

### 2:40 – 3:00 | Conclusion
- **Visual:** Return to the full overview screen displaying the 7-phase evidence chain and the core maxim:
  > **AI PROPOSES. EVIDENCE DECIDES.**
- **Voiceover:**
  > "By combining the generative power of **NVIDIA Nemotron via Nebius Token Factory** with a hardened, deterministic verification sandbox, EVIDA transforms AI from an unreliable code guesser into a high-assurance software repair engineer.
  >
  > **Don't trust the patch. Verify the evidence.**
  >
  > Thank you."

---

## Production Recording Tips

1. **Pre-load the Demo Repository:** Have `broken_python_repo.zip` downloaded and accessible on Desktop for instant drag-and-drop.
2. **Deterministic Response Times:** With ephemeral isolated subprocess execution, each step completes in under 200 milliseconds.
3. **Screen Resolution:** Record at 1080p (1920x1080) at 60 FPS for sharp terminal text rendering.
4. **Color Coding Emphasis:** Highlight the amber `AI PROPOSAL` versus blue `DETERMINISTIC EXECUTION` and emerald `CRYPTOGRAPHIC INTEGRITY` badges to reinforce the core hackathon maxim.

