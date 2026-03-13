---
name: setup
description: "Walk through installing and configuring Proven — checks Python package, Dafny, LLM config, and validates the full setup"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, ToolSearch
---

# Proven Setup

Interactive setup that detects what's already installed and walks through missing pieces.

**Plugin root:** `${CLAUDE_PLUGIN_ROOT}`

## Procedure

Run all four checks below in order. For each step, detect current state first — skip steps that are already complete. Report a summary at the end.

### Step 1: Python Package

Check whether proven is installed:

```bash
python3 -c "import proven; print('installed')" 2>/dev/null
```

- **If installed:** Report version and move on.
- **If not installed:** Install in editable mode from the plugin root:
  ```bash
  pip install -e "${CLAUDE_PLUGIN_ROOT}"
  ```
  Confirm installation succeeded before continuing.

### Step 2: Dafny

Check whether Dafny is available:

```bash
dafny --version 2>/dev/null
```

Also check if `DAFNY_PATH` is set in the environment or in `${CLAUDE_PLUGIN_ROOT}/.env`:

```bash
grep -s '^DAFNY_PATH=' "${CLAUDE_PLUGIN_ROOT}/.env" 2>/dev/null
```

If a custom `DAFNY_PATH` is configured, test that path instead of bare `dafny`.

- **If working:** Report the version and move on.
- **If not found:** Guide the user through installation:

  1. Detect the platform (`uname -s`, `uname -m`).
  2. Provide the correct download instructions:
     - **Linux x64/arm64:** Download from [Dafny releases](https://github.com/dafny-lang/dafny/releases) — the `dafny-*-x64-ubuntu-20.04.zip` or ARM equivalent. Unzip, then either add to PATH or set `DAFNY_PATH` in `.env`.
     - **macOS (Apple Silicon or Intel):** `brew install dafny` is simplest. Alternatively download the zip from GitHub releases.
     - **WSL2:** Same as Linux. Note: the Windows Dafny binary won't work inside WSL — must use the Linux build.
  3. After the user installs, re-run the version check to confirm.
  4. If the binary is not on PATH, ask the user for the install path. Write it to `DAFNY_PATH` in `.env` (creating the file if needed, see Step 3).

### Step 3: LLM Configuration

Check whether `${CLAUDE_PLUGIN_ROOT}/.env` exists and has the required variables set:

```bash
# Check for required variables (non-empty, not placeholder values)
grep -E '^LLM_BASE_URL=.+' "${CLAUDE_PLUGIN_ROOT}/.env" 2>/dev/null
grep -E '^LLM_API_KEY=.+' "${CLAUDE_PLUGIN_ROOT}/.env" 2>/dev/null
grep -E '^LLM_MODEL=.+' "${CLAUDE_PLUGIN_ROOT}/.env" 2>/dev/null
```

A variable counts as "not configured" if it's missing, empty, or still has a placeholder value like `sk-...`.

- **If all configured:** Report the endpoint and model (mask the API key — show only last 4 chars) and move on.
- **If `.env` missing:** Copy the example:
  ```bash
  cp "${CLAUDE_PLUGIN_ROOT}/.env.example" "${CLAUDE_PLUGIN_ROOT}/.env"
  ```
- **For each missing/placeholder variable**, ask the user:
  - `LLM_BASE_URL` — Ask whether they're using a local model (Ollama: `http://localhost:11434/v1`) or a cloud API (OpenAI, Anthropic-compatible, etc). Set accordingly.
  - `LLM_API_KEY` — Ask for their API key. If using local Ollama, any non-empty value works (e.g. `ollama`).
  - `LLM_MODEL` — Ask which model. Suggest `qwen2.5-coder:14b` for local or `claude-sonnet-4-6` for cloud.

Write each value to `.env` using the Edit tool (to preserve other values) or Write if creating fresh.

**Do NOT display the full API key in output.** When confirming, show only the last 4 characters.

### Step 4: Validation

Run the built-in check command:

```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m proven check
```

- **If successful:** Report ready status.
- **If failed:** Show the error and suggest fixes based on which component failed.

## Summary

After all steps, print a status table:

```
Proven Setup Complete
---------------------
Python package:  OK
Dafny:           OK (v4.x.x)
LLM config:     OK (model-name @ endpoint)
Validation:     OK
```

Or for any failures:

```
Proven Setup — Issues Found
----------------------------
Python package:  OK
Dafny:           MISSING — install instructions above
LLM config:     OK
Validation:     FAILED — Dafny not found
```
