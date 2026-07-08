#!/bin/bash
# Developer Heartbeat — runs every 30 minutes (managed by Manager)
# Developer: designs new features, refines applications, conceptualizes OS improvements.
# Automated architectural heartbeat — checks for design requests and review needs.

set -euo pipefail
export PATH="/usr/bin:/bin:/usr/local/bin"

SID_DIR="/root/SID-OS"
LOG="/tmp/sid-developer-beat.log"
COMMS="/etc/sid/team/comms.md"
GH_REPO="Ryuupyroxi/SID-OS"
NOW=$(date -u '+%Y-%m-%d %H:%M UTC')

export GH_TOKEN="$(cat /root/.sid-token 2>/dev/null | grep GH_TOKEN | cut -d= -f2- | tr -d '"' || true)"
export GH_PROMPT_DISABLED=1

log() { echo "[${NOW}] $*" >> "$LOG"; }

log "=== DEVELOPER BEAT ==="

cd "$SID_DIR" 2>/dev/null || { log "FAIL: cd"; exit 1; }
git fetch origin 2>/dev/null

# 1. Check open issues with enhancement/feature label for design input needed
FEATURE_REQUESTS=$(gh issue list --repo "$GH_REPO" --state open --label enhancement --json number,title,updatedAt 2>/dev/null | python3 -c "
import json,sys,datetime
now=datetime.datetime.now(datetime.timezone.utc)
try:
    for i in json.load(sys.stdin):
        age=now-datetime.datetime.fromisoformat(i['updatedAt'].replace('Z','+00:00'))
        print(f'#{i[\"number\"]}: {i[\"title\"][:60]} ({int(age.total_seconds()/3600)}h old)')
except: pass
" 2>/dev/null)
if [ -n "$FEATURE_REQUESTS" ]; then
    log "Feature requests needing design:"
    echo "$FEATURE_REQUESTS" | while read -r l; do log "  $l"; done
fi

# 2. Check open PRs that need architectural review
NEEDS_REVIEW=$(gh pr list --repo "$GH_REPO" --state open --json number,title,createdAt,labels 2>/dev/null | python3 -c "
import json,sys,datetime
now=datetime.datetime.now(datetime.timezone.utc)
try:
    for p in json.load(sys.stdin):
        labels=[l['name'].lower() for l in p.get('labels',[])]
        if 'architecture' in labels or 'design' in labels:
            age=now-datetime.datetime.fromisoformat(p['createdAt'].replace('Z','+00:00'))
            print(f'PR#{p[\"number\"]}: {p[\"title\"][:60]} ({int(age.total_seconds()/3600)}h old)')
except: pass
" 2>/dev/null)
if [ -n "$NEEDS_REVIEW" ]; then
    log "PRs needing architectural review:"
    echo "$NEEDS_REVIEW" | while read -r l; do log "  $l"; done
fi

# 3. Check /etc/sid/team/comms.md for Developer-directed messages
if [ -f "$COMMS" ]; then
    MSGS=$(awk '/→ Developer/{p=1} p{print; if(/^---/){p=0}}' "$COMMS" 2>/dev/null | grep -c "Status:" || true)
    [ "$MSGS" -gt 0 ] && log "Messages for Developer: $MSGS"
fi

log "Beat complete"


# ── Generate agent context file ──────────────────────────
# Written to /tmp/sid-{agent}-context.md so agent wakes up with relevant state
AGENT="developer"
CTX="/tmp/sid-${AGENT}-context.md"
TASKS="/etc/sid/team/tasks"
AGENTS="/etc/sid/team/agents"

{
    echo "# ${AGENT} context — $(date -u '+%Y-%m-%d %H:%M UTC')"
    echo ""
    echo "## Mandate"
    echo "Developer: design features, refine applications, conceptualize OS improvements. Do NOT bug-fix."
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
