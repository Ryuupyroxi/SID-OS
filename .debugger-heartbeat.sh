#!/bin/bash
# Debugger Heartbeat — runs every 30 minutes (managed by Manager)
# Debugger: finds, isolates, and logs errors/bugs as GitHub issues. Automated QA heartbeat.
# SID OS Team Heartbeat — runs every 30min via cron
# Lightweight: checks /etc/sid/team/comms.md for messages, logs status heartbeat

cd /root/SID-OS || exit 1

HEARTBEAT_LOG="/tmp/sid-debugger-beat.log"
COMMS_FILE="/etc/sid/team/comms.md"
LAST_RUN_FILE="/tmp/sid-last-heartbeat"

log() { echo "[$(date '+%Y-%m-%d %H:%M UTC')] $*" >> "$HEARTBEAT_LOG"; }
now_iso() { date -u '+%Y-%m-%d %H:%M UTC'; }

# ── Count unread messages for Debugger ──────────────────────
count_new() {
    local since="1970-01-01"
    [[ -f "$LAST_RUN_FILE" ]] && since=$(cat "$LAST_RUN_FILE" 2>/dev/null || echo "1970-01-01")
    local count=0 cd=""
    while IFS= read -r line; do
        if [[ "$line" =~ ^##\  ]]; then cd="${line### }"
        elif [[ "$line" =~ ^###\ From:\  ]] && echo "$line" | grep -qi "debugger" && ! echo "$line" | grep -qi "From: Debugger"; then
            [[ -n "$cd" && ( "$cd" > "$since" || "$cd" == "$since" ) ]] && count=$((count + 1))
        fi
    done < "$COMMS_FILE"
    echo "$count"
}

# ── Count open issues referenced in /etc/sid/team/comms.md ───────────
count_open_issues() {
    local n
    n=$(grep -c '**Status:** Open' "$COMMS_FILE" 2>/dev/null)
    echo "${n:-0}"
}

# ── Main ────────────────────────────────────────────────────

log "Heartbeat starting"

msg_count=$(count_new)
log "New messages for Debugger: $msg_count"

issue_count=$(count_open_issues)
log "Open issues in comms: $issue_count"

git_status=$(timeout 3 git status --porcelain 2>/dev/null | head -5 || echo "")
[[ -n "$git_status" ]] && log "Uncommitted: $(echo "$git_status" | wc -l) file(s)" || log "Repo clean"

# Write heartbeat status to comms.md only (no auto-writes)
{
    echo ""
    echo "---"
    echo "## $(now_iso)"
    echo ""
    echo "### From: Debugger (Heartbeat) → Team"
    echo "**Subject:** [HEARTBEAT] Status check"
    echo "**Body:** Automated check-in."
    echo "Open issues: ${issue_count} | Unread msgs: ${msg_count}"
    echo "Git: $(echo "$git_status" | tr '\\n' ' ' | head -c 120)"
    echo "**Status:** Alive | Next heartbeat in ~30m"
} >> "$COMMS_FILE"

now_iso > "$LAST_RUN_FILE"
log "Heartbeat complete"

# ── Check GitHub API via GH_TOKEN (if available) ──────────
if [[ -n "$GH_TOKEN" ]]; then
    # List organization issues for SID-OS with fallback timeout
    log "Checking GitHub API (organization issues)..."
    if issue_list=$(timeout 15 gh issue list -R Ryuupyroxi/SID-OS --state open --limit 20 2>/dev/null); then
        issue_count GH=$(echo "$issue_list" | grep -c "^#" 2>/dev/null || echo 0)
        log "GitHub open issues: $issue_count GH"
    else
        log "GitHub API check failed or timed out"
    fi
else
    log "GH_TOKEN not set — skipping GitHub API check"
fi
