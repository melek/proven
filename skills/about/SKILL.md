---
name: about
description: "Introduction to Proven — what it is, what the research found, and optionally how to install the CLI and Dafny. Use when the user asks about Proven, wants to understand the research, or needs to set up the pipeline."
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, ToolSearch"
---

# Proven: About

## What to Present

Proven is a research experiment that explored whether LLMs can produce formally verified software. It is a 5-stage pipeline that takes natural-language requirements and produces Dafny-verified, compiled code.

The five stages: requirements capture, formal specification, specification preprocessing, implementation with proof, and code generation. The novel contribution is Stage 2.5 — deterministic specification preprocessing — which rewrites Dafny specifications into forms that are easier for the Z3 SMT solver to discharge, using ~19 rewrite rules with zero LLM calls.

**Plugin root:** `${CLAUDE_PLUGIN_ROOT}`
**Source repo:** The plugin root contains a full clone of the proven repository.

### Research Findings (present in plain language)

Present these findings descriptively, not as advocacy:

- **Preprocessing doubled the success rate for smaller models.** A 14B-parameter model went from producing verified code for 2 out of 9 benchmarks to 5 out of 9 when specification preprocessing was applied. The same rewrite rules had no measurable effect when paired with a frontier model (Sonnet), which already succeeded on 7 out of 9.
- **Every implementation produced was functionally correct.** Across all conditions — local model, frontier model, with or without preprocessing, and a TDD baseline — zero independent test failures were observed (129 tests across 9 benchmarks). The methods differ in how often they produce code, not in how correct that code is.
- **The pipeline's failure mode is non-production, not incorrect production.** When Proven fails, it fails to verify — it does not produce wrong code that passes verification.

If the user asks for statistical details, provide: N=216 ablation study, p=0.067, Cohen's h=0.49 (medium effect size, not yet reaching conventional significance). The rewrite rules were designed after observing failure patterns on the same benchmark suite, so these numbers reflect performance on the training distribution.

### Current State

Be direct about what this is:

- **Research prototype, not production tool.** The pipeline works on well-structured requirements for data structure problems. It has not been tested on large-scale software.
- **Input is requirements, not code.** Proven produces new verified implementations from English descriptions. It does not annotate, verify, or transform existing codebases.
- **Hard problems still fail.** Ring buffers, red-black trees, and other complex data structures fail for smaller models even with preprocessing. Frontier models handle more but not all.
- **Rewrite rules may be overfit.** The ~19 rewrite rules were designed on the same 9-benchmark suite used for evaluation. Whether they generalize to unseen specifications is unknown.

### Research Participation

Include exactly one sentence:

"Anonymized usage observations can be contributed to the research — see `/proven:contribute` for details."

Do not elaborate on data shape, collection mechanics, or what gets contributed. That belongs in the contribute skill.

## Optional: Installation Walkthrough

If the user asks about installation, setting up the pipeline, or wants to try running it, walk through the setup process below. Do not presume the user wants to install — offer it as an option after presenting the overview.

### Step 1: Python Package

Check whether proven is installed:

```bash
command -v proven 2>/dev/null && proven check 2>/dev/null | head -1
python3 -c "import proven; print('importable')" 2>/dev/null
```

- **If available:** Report and move on.
- **If not installed:** Detect available package managers and install in preference order:
  1. **`uv` (preferred):** `uv tool install -e "${CLAUDE_PLUGIN_ROOT}"` — installs as a global command with auto-managed venv. Editable so source changes take effect immediately.
  2. **`pipx`:** `pipx install -e "${CLAUDE_PLUGIN_ROOT}"`
  3. **`pip`:** `pip install -e "${CLAUDE_PLUGIN_ROOT}"` — may fail on externally-managed Python. If so, suggest uv or pipx.

  If the system Python is externally managed and neither uv nor pipx is available, guide the user to install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`

  After installation, verify: `proven check` or `python3 -c "import proven"`.

### Step 2: Dafny

Check whether Dafny is available:

```bash
dafny --version 2>/dev/null
```

Also check if `DAFNY_PATH` is set:

```bash
grep -s '^DAFNY_PATH=' ~/.config/proven/.env 2>/dev/null
grep -s '^DAFNY_PATH=' .env 2>/dev/null
```

- **If working:** Report the version and move on.
- **If not found:** Guide the user through installation:
  1. Detect the platform (`uname -s`, `uname -m`).
  2. If `gh` is available, offer to auto-download from `dafny-lang/dafny` releases.
  3. If `gh` is not available, provide manual download instructions:
     - **Linux x64/arm64:** Download from [Dafny releases](https://github.com/dafny-lang/dafny/releases). Unzip, add to PATH or set `DAFNY_PATH`.
     - **macOS:** `brew install dafny` is simplest. Alternatively download the zip.
     - **WSL2:** Same as Linux. The Windows Dafny binary won't work inside WSL.
  4. After install, verify with `dafny --version` or `$DAFNY_PATH --version`.
  5. If the binary is not on PATH, ask the user for the install location and set `DAFNY_PATH` in `.env`.

### Step 3: LLM Configuration

Proven loads `.env` from the current working directory via `python-dotenv`. Check common locations:

```bash
for f in .env ~/.config/proven/.env; do
  [ -f "$f" ] && echo "Found: $f" && grep -E '^LLM_(BASE_URL|API_KEY|MODEL)=' "$f" 2>/dev/null
done
```

- **If all configured:** Report endpoint and model (mask API key — show only last 4 chars).
- **If incomplete:** Ask which LLM provider:
  - **Anthropic (Claude):** Set `LLM_API_KEY` (starts with `sk-ant-`), `LLM_MODEL` (e.g. `claude-sonnet-4-6`). `LLM_BASE_URL` not used for Anthropic models.
  - **Local Ollama:** `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, `LLM_MODEL` (e.g. `qwen2.5-coder:14b`).
  - **OpenAI / OpenAI-compatible:** Set all three variables for the provider.

  Use `.env.example` from the plugin root as a template. **Do NOT display the full API key in output.**

### Step 4: Validation

```bash
proven check
```

If `proven` isn't on PATH, fall back to `python3 -m proven check`.

Report a summary table at the end:

```
Proven Setup Complete
---------------------
Python package:  OK
Dafny:           OK (v4.x.x)
LLM config:     OK (model-name @ endpoint)
Validation:     OK
```

Or for failures:

```
Proven Setup — Issues Found
----------------------------
Python package:  OK
Dafny:           MISSING — install instructions above
LLM config:     OK
Validation:     FAILED — Dafny not found
```
