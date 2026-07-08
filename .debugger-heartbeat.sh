#!/bin/bash
# Debugger Heartbeat — runs every 30 minutes (managed by Manager)
# Debugger: finds, isolates, and logs errors/bugs as GitHub issues. Automated QA heartbeat.
# SID OS Team Heartbeat — runs every 30min via cron
# Lightweight: checks /etc/sid/team/comms.md for messages, logs status heartbeat

cd /root/SID-OS || exit 1

HEARTBEAT_LOG="/tmp/sid-heartbeat.log"
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

# Append heartbeat to /etc/sid/team/comms.md
{
    echo ""
    echo "---"
    echo "## $(now_iso)"
    echo ""
    echo "### From: Debugger (Heartbeat) → Team"
    echo "**Subject:** [HEARTBEAT] Status check"
    echo "**Body:** Automated check-in."
    echo "Open issues: ${issue_count} | Unread msgs: ${msg_count}"
    echo "Git: $(echo "$git_status" | tr '\n' ' ' | head -c 120)"
    echo "**Status:** Alive | Next heartbeat in ~30m"
} >> "$COMMS_FILE"

now_iso > "$LAST_RUN_FILE"
log "Heartbeat complete"


# ── Generate agent context file ──────────────────────────
# Written to /tmp/sid-{agent}-context.md so agent wakes up with relevant state
AGENT="debugger"
CTX="/tmp/sid-${AGENT}-context.md"
TASKS="/etc/sid/team/tasks"
AGENTS="/etc/sid/team/agents"

{
    echo "# ${AGENT} context — $(date -u '+%Y-%m-%d %H:%M UTC')"
    echo ""
    echo "## Mandate"
    echo "Debugger: find, isolate, log bugs as GitHub issues. Do NOT implement fixes."
    echo ""
    echo "## Open tasks"
    if [ -d "$TASKS" ]; then
        for tf in "$TASKS"/*.task; do
            [ -f "$tf" ] || continue
            s=$(grep "^STATUS:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
            a=$(grep "^ASSIGNEE:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
            [ "$a" = "$AGENT" ] || continue
            echo "- $(basename "$tf" .task): $s"
            grep "^DESCRIPTION:" "$tf" 2>/dev/null | cut -d: -f2-
        done
    fi
    echo ""
    echo "## Other agents"
    for oa in debugger coder developer manager; do
        [ "$oa" = "$AGENT" ] && continue
        lf="${AGENTS}/${oa}/log.md"
        last="(no log)"
        [ -f "$lf" ] && last=$(grep "^## " "$lf" 2>/dev/null | head -1 || echo "(no entries)")
        echo "- $oa: $last"
    done
    echo ""
    echo "## Recent work log"
    lf="${AGENTS}/${AGENT}/log.md"
    if [ -f "$lf" ]; then
        grep -A2 "^## " "$lf" 2>/dev/null | head -12
    fi
} > "$CTX"
