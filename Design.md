# EVIDA — Visual Design & Design System

## 1. Design Philosophy

EVIDA is an evidence-first, high-precision engineering platform. The visual aesthetic reflects **rigor, clarity, and certainty**:
- **Tone:** Technical, confident, minimal, forensic.
- **Theme:** Dark mode default with high-contrast data visualization.
- **Metaphor:** Scientific verification laboratory / cryptographic ledger.

---

## 2. Color Palette

### 2.1 Core Neutral System
- **Background Root:** `#090D16` (Deep Obsidian Void)
- **Surface Elevation 1 (Card/Panel):** `#111827` (Charcoal Slate)
- **Surface Elevation 2 (Hover/Active):** `#1F2937` (Muted Zinc)
- **Border / Divider:** `#374151` (Subtle boundary line)
- **Text Primary:** `#F9FAFB` (High-contrast pure white)
- **Text Secondary:** `#9CA3AF` (Muted cool gray)
- **Text Muted:** `#6B7280` (Deep gray for timestamps & tags)

### 2.2 Semantic & Evidence Accents
- **Evidence Verified (Emerald):** `#10B981` (Bright emerald for mathematically/empirically verified fixes)
- **Evidence Unverified / Error (Rose):** `#EF4444` (Vibrant crimson for failed tests or unverified patches)
- **Investigation / Active (Amber):** `#F59E0B` (Warm amber for active investigations, running sandboxes)
- **AI Proposal (Indigo/Cyan):** `#6366F1` to `#06B6D4` (Gradient signifying untrusted AI propositions)
- **NVIDIA Brand Highlight:** `#76B900` (NVIDIA green for model and inference telemetry)

---

## 3. Typography

- **Interface Body:** `Inter`, system-ui, -apple-system, sans-serif.
- **Code & Logs:** `JetBrains Mono`, `Fira Code`, monospace.
- **Status Badges:** Uppercase, tracking-widest, semibold monospace (`VERIFIED`, `UNVERIFIED`, `REPRODUCING`).

---

## 4. UI Components

- **Audit Badge:** Prominent pill badge displaying verification state with evidence icon.
- **Evidence Card:** Dual-panel component displaying the AI hypothesis on the left and sandbox deterministic proof (exit code, test logs) on the right.
- **Telemetry Bar:** Displays active NVIDIA model identifier (`NEBIUS_MODEL`), latency, token usage, and sandbox execution duration in milliseconds.
