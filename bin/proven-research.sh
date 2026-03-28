#!/bin/sh
# proven-research.sh — Research observation management for Proven Experiment 004
#
# Subcommands: enable, disable, status, preview, submit, purge, rotate-id
#
# POSIX sh compatible. Works on Linux and macOS.
# Called from the /proven:contribute skill or standalone.

set -e

# --- Configuration ---

DATA_DIR="${HOME}/.proven"
OBS_DIR="${DATA_DIR}/observations"
SUBMITTED_DIR="${OBS_DIR}/submitted"
CONFIG_FILE="${DATA_DIR}/config.json"
CONSENT_FILE="${DATA_DIR}/consent.json"
INSTALL_ID_FILE="${DATA_DIR}/installation_id"
SALT_FILE="${DATA_DIR}/salt"

CONSENT_VERSION="1"
REPO="melek/proven"

# --- Helpers ---

die() {
    printf 'error: %s\n' "$1" >&2
    exit 1
}

ensure_dir() {
    mkdir -p "$1"
}

# Read a key from the JSON config file (minimal, no jq dependency)
config_get() {
    key="$1"
    if [ -f "$CONFIG_FILE" ]; then
        # Extract value for "key": "value" or "key": true/false
        sed -n "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([^\",}]*\)\"\{0,1\}.*/\1/p" "$CONFIG_FILE" | head -1
    fi
}

# Write or update a key in the config file
config_set() {
    key="$1"
    value="$2"
    ensure_dir "$DATA_DIR"
    if [ ! -f "$CONFIG_FILE" ]; then
        printf '{\n  "%s": %s\n}\n' "$key" "$value" > "$CONFIG_FILE"
    elif grep -q "\"${key}\"" "$CONFIG_FILE" 2>/dev/null; then
        # Update existing key — portable sed in-place
        tmp="${CONFIG_FILE}.tmp.$$"
        sed "s/\"${key}\"[[:space:]]*:[[:space:]]*[^,}]*/\"${key}\": ${value}/" "$CONFIG_FILE" > "$tmp"
        mv "$tmp" "$CONFIG_FILE"
    else
        # Add key before closing brace
        tmp="${CONFIG_FILE}.tmp.$$"
        # Use awk for portability (BSD sed doesn't handle \n in replacement)
        awk -v k="$key" -v v="$value" '{
            if (/}$/) { sub(/}$/, ","); print; printf "  \"%s\": %s\n}\n", k, v }
            else print
        }' "$CONFIG_FILE" > "$tmp"
        mv "$tmp" "$CONFIG_FILE"
    fi
}

is_enabled() {
    val="$(config_get "observations_enabled")"
    [ "$val" = "true" ]
}

count_observations() {
    dir="$1"
    if [ -d "$dir" ]; then
        # Count .json files, excluding subdirectories
        find "$dir" -maxdepth 1 -name '*.json' -type f 2>/dev/null | wc -l | tr -d ' '
    else
        printf '0'
    fi
}

date_range() {
    dir="$1"
    if [ -d "$dir" ]; then
        files="$(find "$dir" -maxdepth 1 -name '*.json' -type f 2>/dev/null | sort)"
        if [ -n "$files" ]; then
            first="$(echo "$files" | head -1 | xargs basename | sed 's/\.json$//' | cut -c1-10)"
            last="$(echo "$files" | tail -1 | xargs basename | sed 's/\.json$//' | cut -c1-10)"
            printf '%s to %s' "$first" "$last"
        else
            printf 'none'
        fi
    else
        printf 'none'
    fi
}

generate_uuid() {
    # Generate a UUIDv4 using available sources
    if command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    elif [ -r /proc/sys/kernel/random/uuid ]; then
        cat /proc/sys/kernel/random/uuid
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import uuid; print(uuid.uuid4())"
    else
        # Fallback: construct from /dev/urandom
        od -x /dev/urandom 2>/dev/null | head -1 | awk '{print $2$3"-"$4"-"$5"-"$6"-"$7$8$9}' | head -c 36
        printf '\n'
    fi
}

get_installation_id() {
    if [ -f "$INSTALL_ID_FILE" ]; then
        cat "$INSTALL_ID_FILE"
    fi
}

ensure_salt() {
    if [ ! -f "$SALT_FILE" ]; then
        ensure_dir "$DATA_DIR"
        generate_uuid > "$SALT_FILE"
        chmod 600 "$SALT_FILE"
    fi
    cat "$SALT_FILE"
}

hash_id() {
    raw_id="$1"
    salt="$(ensure_salt)"
    # SHA-256 hash, first 8 characters
    if command -v sha256sum >/dev/null 2>&1; then
        printf '%s%s' "$raw_id" "$salt" | sha256sum | cut -c1-8
    elif command -v shasum >/dev/null 2>&1; then
        printf '%s%s' "$raw_id" "$salt" | shasum -a 256 | cut -c1-8
    elif command -v python3 >/dev/null 2>&1; then
        printf '%s%s' "$raw_id" "$salt" | python3 -c "import sys,hashlib; print(hashlib.sha256(sys.stdin.read().encode()).hexdigest()[:8])"
    else
        die "no SHA-256 tool available (need sha256sum, shasum, or python3)"
    fi
}

timestamp_iso() {
    date -u '+%Y-%m-%dT%H:00:00Z' 2>/dev/null || date '+%Y-%m-%dT%H:00:00'
}

# --- Subcommands ---

cmd_enable() {
    ensure_dir "$OBS_DIR"
    ensure_dir "$SUBMITTED_DIR"
    config_set "observations_enabled" "true"

    # Write consent record
    ts="$(timestamp_iso)"
    cat > "$CONSENT_FILE" <<CONSENT_EOF
{
  "consent_given": true,
  "consent_version": "${CONSENT_VERSION}",
  "timestamp": "${ts}",
  "what_collected": "counts and enum categories from skill invocations (patterns_found, gaps, options, language, loc bucket, action)",
  "what_not_collected": "source code, file paths, file contents, conversation text, error messages, project names"
}
CONSENT_EOF

    printf 'Observation collection enabled.\n'
    printf 'Consent record written to %s\n' "$CONSENT_FILE"
    printf 'Observations will be stored in %s\n' "$OBS_DIR"
}

cmd_disable() {
    config_set "observations_enabled" "false"
    printf 'Observation collection disabled.\n'
    printf 'Existing observations have NOT been deleted. Use "purge" to remove them.\n'
}

cmd_status() {
    printf 'Proven Research — Observation Status\n'
    printf '====================================\n\n'

    if is_enabled; then
        printf 'Collection:      enabled\n'
    else
        printf 'Collection:      disabled\n'
    fi

    pending="$(count_observations "$OBS_DIR")"
    submitted="$(count_observations "$SUBMITTED_DIR")"
    printf 'Pending:         %s observations\n' "$pending"
    printf 'Submitted:       %s observations\n' "$submitted"

    if [ "$pending" -gt 0 ] 2>/dev/null; then
        printf 'Date range:      %s\n' "$(date_range "$OBS_DIR")"
    fi

    install_id="$(get_installation_id)"
    if [ -n "$install_id" ]; then
        hashed="$(hash_id "$install_id")"
        printf 'Installation ID: %s\n' "$hashed"
    else
        printf 'Installation ID: not yet generated (created on first submit)\n'
    fi

    if [ -f "$CONSENT_FILE" ]; then
        printf 'Consent:         recorded\n'
    else
        printf 'Consent:         not recorded\n'
    fi
}

cmd_preview() {
    pending="$(count_observations "$OBS_DIR")"
    if [ "$pending" = "0" ]; then
        printf 'No pending observations to preview.\n'
        return 0
    fi

    # Validate observations
    errors=0
    validated=0
    valid_actions="edited committed no-action asked-followup"
    valid_loc="<50 50-200 200-1000 1000+"
    valid_skills="advise survey"

    preview_file="$(mktemp /tmp/proven-report-preview-XXXXXXXX.json)"

    printf '[\n' > "$preview_file"
    first=true

    for f in "$OBS_DIR"/*.json; do
        [ -f "$f" ] || continue

        # Basic validation: no "/" in values, no value >100 chars
        has_slash=false
        has_long=false

        # Check for slashes in values (crude but effective)
        if grep -q '": "[^"]*/' "$f" 2>/dev/null; then
            has_slash=true
            errors=$((errors + 1))
            printf 'WARN: %s contains "/" in a value (possible file path leak)\n' "$(basename "$f")" >&2
        fi

        # Check for values >100 chars
        if grep -E '": "[^"]{101,}"' "$f" >/dev/null 2>&1; then
            has_long=true
            errors=$((errors + 1))
            printf 'WARN: %s contains a value >100 characters (possible content leak)\n' "$(basename "$f")" >&2
        fi

        # Check enum values
        has_bad_enum=false
        obs_skill="$(grep '"skill"' "$f" 2>/dev/null | sed 's/.*": *"//;s/".*//' )"
        obs_action="$(grep '"action"' "$f" 2>/dev/null | sed 's/.*": *"//;s/".*//' )"
        obs_loc="$(grep '"loc"' "$f" 2>/dev/null | sed 's/.*": *"//;s/".*//' )"

        check_enum() {
            val="$1"; valid="$2"; field="$3"
            if [ -n "$val" ]; then
                found=false
                for v in $valid; do
                    [ "$val" = "$v" ] && found=true
                done
                if [ "$found" = "false" ]; then
                    has_bad_enum=true
                    errors=$((errors + 1))
                    printf 'WARN: %s has invalid %s: "%s"\n' "$(basename "$f")" "$field" "$val" >&2
                fi
            fi
        }
        check_enum "$obs_skill" "$valid_skills" "skill"
        check_enum "$obs_action" "$valid_actions" "action"
        check_enum "$obs_loc" "$valid_loc" "loc"

        if [ "$has_slash" = "false" ] && [ "$has_long" = "false" ] && [ "$has_bad_enum" = "false" ]; then
            validated=$((validated + 1))
        fi

        # Append to preview
        if [ "$first" = "true" ]; then
            first=false
        else
            printf ',\n' >> "$preview_file"
        fi
        cat "$f" >> "$preview_file"
    done

    printf '\n]\n' >> "$preview_file"

    printf '\nPreview Summary\n'
    printf '===============\n'
    printf 'Total observations: %s\n' "$pending"
    printf 'Passed validation:  %s\n' "$validated"
    printf 'Validation errors:  %s\n' "$errors"
    printf 'Date range:         %s\n' "$(date_range "$OBS_DIR")"
    printf 'Preview written to: %s\n' "$preview_file"

    if [ "$errors" -gt 0 ]; then
        printf '\nWARNING: %s observation(s) failed validation. Review the preview file before submitting.\n' "$errors"
    fi
}

cmd_submit() {
    # Check prerequisites
    command -v gh >/dev/null 2>&1 || die "gh CLI is required for submission. Install from https://cli.github.com/"

    # Check gh auth
    gh auth status >/dev/null 2>&1 || die "gh CLI is not authenticated. Run 'gh auth login' first."

    pending="$(count_observations "$OBS_DIR")"
    if [ "$pending" = "0" ]; then
        printf 'No pending observations to submit.\n'
        return 0
    fi

    # Ensure installation ID exists
    if [ ! -f "$INSTALL_ID_FILE" ]; then
        ensure_dir "$DATA_DIR"
        generate_uuid > "$INSTALL_ID_FILE"
        chmod 600 "$INSTALL_ID_FILE"
        printf 'Generated new installation ID.\n\n'
    fi

    install_id="$(get_installation_id)"
    hashed_id="$(hash_id "$install_id")"

    # Show preview
    printf 'Preparing submission...\n\n'
    cmd_preview
    printf '\n'

    # Show GitHub identity
    gh_user="$(gh api user --jq '.login' 2>/dev/null || echo 'unknown')"
    printf 'GitHub identity: %s\n' "$gh_user"
    printf 'Installation ID: %s\n' "$hashed_id"
    printf 'Repository: %s\n' "$REPO"
    printf '\n'

    # Consent confirmation
    printf 'This will create a public GitHub issue containing the observation data above.\n'
    printf 'Your GitHub identity (%s) will be attached to the issue.\n' "$gh_user"
    printf 'This data is public and permanent once submitted.\n\n'
    printf 'Proceed with submission? [y/N] '
    read -r confirm
    case "$confirm" in
        [yY]|[yY][eE][sS]) ;;
        *) printf 'Submission cancelled.\n'; return 0 ;;
    esac

    # Build the observation data
    ts="$(timestamp_iso)"
    obs_data="$(mktemp /tmp/proven-submit-XXXXXXXX.json)"

    printf '{\n' > "$obs_data"
    printf '  "submission_type": "experiment-004-observations",\n' >> "$obs_data"
    printf '  "hashed_installation_id": "%s",\n' "$hashed_id" >> "$obs_data"
    printf '  "consent_version": "%s",\n' "$CONSENT_VERSION" >> "$obs_data"
    printf '  "submitted_at": "%s",\n' "$ts" >> "$obs_data"
    printf '  "observation_count": %s,\n' "$pending" >> "$obs_data"
    printf '  "observations": ' >> "$obs_data"

    # Collect observations array
    printf '[\n' >> "$obs_data"
    first=true
    for f in "$OBS_DIR"/*.json; do
        [ -f "$f" ] || continue
        if [ "$first" = "true" ]; then
            first=false
        else
            printf ',\n' >> "$obs_data"
        fi
        cat "$f" >> "$obs_data"
    done
    printf '\n  ]\n' >> "$obs_data"
    printf '}\n' >> "$obs_data"

    # Create GitHub issue
    issue_title="[Experiment 004] Observation submission (${hashed_id}, n=${pending})"
    issue_body="$(cat <<ISSUE_EOF
## Research Observation Submission

**Experiment:** 004 — Methodology Transfer
**Hashed Installation ID:** ${hashed_id}
**Observation Count:** ${pending}
**Submitted:** ${ts}
**Consent Version:** ${CONSENT_VERSION}

### Data

\`\`\`json
$(cat "$obs_data")
\`\`\`

---
*Submitted via proven-research.sh. See [RESEARCH.md](https://github.com/${REPO}/blob/main/docs/RESEARCH.md) for the research statement.*
ISSUE_EOF
)"

    issue_url="$(gh issue create \
        --repo "$REPO" \
        --title "$issue_title" \
        --body "$issue_body" \
        --label "research-data" 2>&1)" || die "Failed to create issue: ${issue_url}"

    printf '\nSubmission successful: %s\n' "$issue_url"

    # Flush submitted observations
    ensure_dir "$SUBMITTED_DIR"
    for f in "$OBS_DIR"/*.json; do
        [ -f "$f" ] || continue
        mv "$f" "$SUBMITTED_DIR/"
    done

    printf 'Observations moved to %s\n' "$SUBMITTED_DIR"

    # Clean up temp file
    rm -f "$obs_data"
}

cmd_purge() {
    pending="$(count_observations "$OBS_DIR")"
    submitted="$(count_observations "$SUBMITTED_DIR")"
    total=$((pending + submitted))

    if [ "$total" = "0" ]; then
        printf 'No observations to purge.\n'
        return 0
    fi

    printf 'This will permanently delete:\n'
    printf '  - %s pending observations\n' "$pending"
    printf '  - %s submitted observations\n' "$submitted"
    printf '\nThis cannot be undone. Proceed? [y/N] '
    read -r confirm
    case "$confirm" in
        [yY]|[yY][eE][sS]) ;;
        *) printf 'Purge cancelled.\n'; return 0 ;;
    esac

    find "$OBS_DIR" -maxdepth 1 -name '*.json' -type f -delete 2>/dev/null
    find "$SUBMITTED_DIR" -maxdepth 1 -name '*.json' -type f -delete 2>/dev/null

    printf 'Purged %s observations.\n' "$total"
}

cmd_rotate_id() {
    old_id="$(get_installation_id)"

    if [ -n "$old_id" ]; then
        old_hashed="$(hash_id "$old_id")"
        printf 'Current installation ID: %s\n' "$old_hashed"
        printf '\nWARNING: Rotating your installation ID breaks longitudinal linking\n'
        printf 'between past and future submissions. Past submissions will remain\n'
        printf 'associated with the old ID.\n\n'
        printf 'Proceed? [y/N] '
        read -r confirm
        case "$confirm" in
            [yY]|[yY][eE][sS]) ;;
            *) printf 'Rotation cancelled.\n'; return 0 ;;
        esac
    fi

    ensure_dir "$DATA_DIR"
    new_id="$(generate_uuid)"
    printf '%s' "$new_id" > "$INSTALL_ID_FILE"
    chmod 600 "$INSTALL_ID_FILE"

    # Also rotate salt so old ID can't be re-derived
    generate_uuid > "$SALT_FILE"
    chmod 600 "$SALT_FILE"

    new_hashed="$(hash_id "$new_id")"
    if [ -n "$old_id" ]; then
        printf 'Installation ID rotated.\n'
        printf 'Old: %s\n' "$old_hashed"
        printf 'New: %s\n' "$new_hashed"
    else
        printf 'Installation ID generated: %s\n' "$new_hashed"
    fi
}

# --- Main ---

usage() {
    printf 'Usage: proven-research.sh <command>\n\n'
    printf 'Commands:\n'
    printf '  enable      Enable observation collection\n'
    printf '  disable     Disable observation collection (keeps existing data)\n'
    printf '  status      Show observation status and counts\n'
    printf '  preview     Validate and preview pending observations\n'
    printf '  submit      Submit observations to GitHub via gh CLI\n'
    printf '  purge       Delete all local observations\n'
    printf '  rotate-id   Generate a new installation ID\n'
}

case "${1:-}" in
    enable)     cmd_enable ;;
    disable)    cmd_disable ;;
    status)     cmd_status ;;
    preview)    cmd_preview ;;
    submit)     cmd_submit ;;
    purge)      cmd_purge ;;
    rotate-id)  cmd_rotate_id ;;
    -h|--help)  usage ;;
    *)          usage; exit 1 ;;
esac
