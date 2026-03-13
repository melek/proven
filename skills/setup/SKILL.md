---
name: setup
description: "Walk through installing and configuring Proven — checks Python package, Dafny, LLM config, and validates the full setup"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, ToolSearch
---

# Proven Setup

Interactive setup that detects what's already installed and walks through missing pieces.

**Plugin root:** `${CLAUDE_PLUGIN_ROOT}`
**Source repo:** The plugin root contains a full clone of the proven repository.

## Procedure

Run all four checks below in order. For each step, detect current state first — skip steps that are already complete. Report a summary at the end.

### Step 1: Python Package

Check whether proven is installed as a CLI command:

```bash
command -v proven 2>/dev/null && proven check 2>/dev/null | head -1
```

Also check importability:

```bash
python3 -c "import proven; print('importable')" 2>/dev/null
```

- **If `proven` CLI is available:** Report and move on.
- **If not installed:** Detect available package managers and install in preference order:

  1. **`uv` (preferred):** `uv tool install -e "${CLAUDE_PLUGIN_ROOT}"` — installs as a global command with auto-managed venv. Editable so source changes take effect immediately.
  2. **`pipx`:** `pipx install -e "${CLAUDE_PLUGIN_ROOT}"`
  3. **`pip`:** `pip install -e "${CLAUDE_PLUGIN_ROOT}"` — may fail on externally-managed Python (Debian/Ubuntu). If so, suggest uv or pipx.

  Check for each with `command -v uv`, `command -v pipx`, `command -v pip` (or `python3 -m pip`).

  If the system Python is externally managed and neither uv nor pipx is available, guide the user to install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`

  After installation, verify: `proven check` or `python3 -c "import proven"`.

### Step 2: Dafny

Check whether Dafny is available:

```bash
dafny --version 2>/dev/null
```

Also check if `DAFNY_PATH` is set in the environment or in `~/.config/proven/.env` or the project working directory `.env`:

```bash
grep -s '^DAFNY_PATH=' ~/.config/proven/.env 2>/dev/null
grep -s '^DAFNY_PATH=' .env 2>/dev/null
```

If a custom `DAFNY_PATH` is configured, test that path instead of bare `dafny`.

- **If working:** Report the version and move on.
- **If not found:** Guide the user through installation:

  1. Detect the platform (`uname -s`, `uname -m`).
  2. Offer to auto-download if `gh` is available:
     ```bash
     gh release download --repo dafny-lang/dafny --pattern "dafny-*-x64-ubuntu-*.zip" --dir /tmp
     python3 -c "import zipfile; zipfile.ZipFile('/tmp/dafny-....zip').extractall('$HOME/dafny')"
     ```
     Determine the correct asset name via `gh api repos/dafny-lang/dafny/releases/latest --jq '.assets[].name'` and match platform.
  3. If `gh` is not available, provide manual download instructions:
     - **Linux x64/arm64:** Download from [Dafny releases](https://github.com/dafny-lang/dafny/releases). Unzip, then either add to PATH or set `DAFNY_PATH`.
     - **macOS:** `brew install dafny` is simplest. Alternatively download the zip.
     - **WSL2:** Same as Linux. The Windows Dafny binary won't work inside WSL — must use the Linux build.
  4. After install, verify with `dafny --version` or `$DAFNY_PATH --version`.
  5. If the binary is not on PATH, ask the user for the install location and set `DAFNY_PATH` in `.env` (see Step 3 for `.env` location).

### Step 3: LLM Configuration

Proven loads `.env` from the current working directory via `python-dotenv`. The `.env` file should live in the user's project directory, **not** in the plugin cache (which gets overwritten on plugin updates).

Determine where to put `.env`:
- If the user has a proven project directory (e.g. a clone of the repo), use that.
- Otherwise, create `~/.config/proven/.env` as a shared config location. Note: proven would need to be run from that directory, or the user can symlink/copy to their working directory.

Check whether `.env` exists and has the required variables:

```bash
# Check common locations
for f in .env ~/.config/proven/.env; do
  [ -f "$f" ] && echo "Found: $f" && grep -E '^LLM_(BASE_URL|API_KEY|MODEL)=' "$f" 2>/dev/null
done
```

A variable counts as "not configured" if it's missing, empty, or still has a placeholder value like `sk-...`.

- **If all configured:** Report the endpoint and model (mask the API key — show only last 4 chars) and move on.
- **If `.env` missing or incomplete:** Walk through configuration:

  Ask the user which LLM provider they want to use:

  - **Anthropic (Claude models):** Proven has native Anthropic SDK support. Models starting with `claude-` are automatically routed to the Anthropic API. Set:
    - `LLM_API_KEY` — Anthropic API key (starts with `sk-ant-`)
    - `LLM_MODEL` — e.g. `claude-sonnet-4-6`, `claude-opus-4-6`
    - `LLM_BASE_URL` — not used for Anthropic models (set to any value or leave as default)

  - **Local Ollama:** Set:
    - `LLM_BASE_URL=http://localhost:11434/v1`
    - `LLM_API_KEY=ollama` (any non-empty value)
    - `LLM_MODEL` — e.g. `qwen2.5-coder:14b`

  - **OpenAI / OpenAI-compatible:** Set:
    - `LLM_BASE_URL` — the API endpoint (e.g. `https://api.openai.com/v1`, `https://openrouter.ai/api/v1`)
    - `LLM_API_KEY` — API key
    - `LLM_MODEL` — model name

  Also set `DAFNY_PATH` in the same `.env` if Dafny is not on PATH (from Step 2).

  Use the `.env.example` from the plugin root as a template:
  ```bash
  cat "${CLAUDE_PLUGIN_ROOT}/.env.example"
  ```

  Write the file using the Edit or Write tool. **Do NOT display the full API key in output.** Show only the last 4 characters when confirming.

### Step 4: Validation

Run the built-in check:

```bash
proven check
```

If `proven` isn't on PATH (e.g. installed via pip into a venv), fall back to:

```bash
python3 -m proven check
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
