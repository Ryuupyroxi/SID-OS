#!/bin/bash
# Manager Heartbeat — runs every 30min via cron
# Pipeline monitor + task board tracker. Silent. Logs to /tmp/sid-manager-beat.log

set -euo pipefail
export PATH="/usr/bin:/bin:/usr/local/bin"

SID_DIR="/root/SID-OS"
LOG="/tmp/sid-manager-beat.log"
COMMS="/etc/sid/team/comms.md"
TASKS="/etc/sid/team/tasks"
AGENTS="/etc/sid/team/agents"
GH_REPO="Ryuupyroxi/SID-OS"
NOW=$(date -u '+%Y-%m-%d %H:%M UTC')
BEAT=$(date +%s)

export GH_TOKEN="$(cat /root/.sid-token 2>/dev/null | grep GH_TOKEN | cut -d= -f2- | tr -d '"' || true)"
export GH_PROMPT_DISABLED=1

log() { echo "[${NOW}] $*" >> "$LOG"; }

log "=== BEAT ==="
cd "$SID_DIR" 2>/dev/null || { log "FAIL: cd"; exit 1; }
git fetch origin 2>/dev/null

# 1. GitHub issues — 30s timeout
STALLED=$(timeout 30 gh issue list --repo "$GH_REPO" --state open --json number,title,updatedAt,assignees 2>/dev/null | python3 -c "
import json,sys,datetime
now=datetime.datetime.now(datetime.timezone.utc)
try:
    for i in json.load(sys.stdin):
        age=now-datetime.datetime.fromisoformat(i['updatedAt'].replace('Z','+00:00'))
        if age.total_seconds()>7200 and not i.get('assignees'):
            print(f'#{i[\"number\"]}: {i[\"title\"][:60]}')
except: pass
" 2>/dev/null || echo "")
[ -n "$STALLED" ] && log "Stalled:" && echo "$STALLED" | while read -r l; do log "  $l"; done

# 2. PRs — 30s timeout
READY=$(timeout 30 gh pr list --repo "$GH_REPO" --state open --json number,title,mergeable,reviews 2>/dev/null | python3 -c "
import json,sys
try:
    for p in json.load(sys.stdin):
        if p.get('mergeable')=='MERGEABLE' and not (p.get('reviews') or []):
            print(f'PR#{p[\"number\"]}: {p[\"title\"][:60]}')
except: pass
" 2>/dev/null || echo "")
[ -n "$READY" ] && log "Ready-merge: $READY"

# 3. Task board
PENDING=$(find "$TASKS" -name "*.task" -exec grep -l "STATUS: pending" {} \; 2>/dev/null | wc -l)
ACTIVE=$(find "$TASKS" -name "*.task" -exec grep -l "STATUS: active" {} \; 2>/dev/null | wc -l)
log "Tasks: ${PENDING}p ${ACTIVE}a"

# Stale locks (>60min)
find "$TASKS" -name "*.task" | while read -r tf; do
    s=$(grep "^STATUS:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
    lb=$(grep "^LOCKED_BY:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
    la=$(grep "^LOCKED_AT:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
    [ "$s" = "active" ] && [ -n "$lb" ] && [ -n "$la" ] || continue
    le=$(date -d "$la" +%s 2>/dev/null || echo 0)
    age=$(( ($(date +%s) - le) / 60 ))
    [ "$age" -gt 60 ] && log "Stale: $(basename "$tf" .task) ${lb} ${age}m"
done

# 4. Agent pulse
for a in debugger coder developer; do
    lf="${AGENTS}/${a}/log.md"
    [ -f "$lf" ] && log "$a: $(grep "^## " "$lf" 2>/dev/null | head -1 || echo idle)"
done

# 5. Messages
[ -f "$COMMS" ] && m=$(awk '/From:.*→ Manager/{p=1} p{print; if(/^---/){p=0}}' "$COMMS" 2>/dev/null | grep -c "Status:" || true)
[ -n "${m:-}" ] && [ "$m" -gt 0 ] && log "Msgs: $m"

log "Done ($(( $(date +%s) - BEAT ))s)"

# ── Android notification on event changes ─────────────────
notify() {
    local title="$1" msg="$2" urgency="${3:-normal}"
    termux-notification -t "SID OS ${title}" -c "${msg}" --priority "${urgency}" --alert-once 2>/dev/null || true
}
NOTIFY_STATE="/tmp/sid-notify-state"
touch "$NOTIFY_STATE"
PREV_PENDING=$(grep "PENDING:" "$NOTIFY_STATE" 2>/dev/null | cut -d: -f2 || echo "-1")
PREV_ACTIVE=$(grep "ACTIVE:" "$NOTIFY_STATE" 2>/dev/null | cut -d: -f2 || echo "-1")
if [ "$PREV_PENDING" != "-1" ] && [ "$PENDING" -lt "$PREV_PENDING" ] 2>/dev/null; then
    notify "📋 Task claimed" "Pending: $PENDING (was $PREV_PENDING)" "normal"
fi
if [ "$PREV_ACTIVE" != "-1" ] && [ "$ACTIVE" -gt "$PREV_ACTIVE" ] 2>/dev/null; then
    notify "🔧 Agent active" "$ACTIVE task(s) now in progress" "high"
fi
echo "PENDING:$PENDING" > "$NOTIFY_STATE"
echo "ACTIVE:$ACTIVE" >> "$NOTIFY_STATE"
# Stale lock notification (once per task)
find "$TASKS" -name "*.task" | while read -r tf; do
    s=$(grep "^STATUS:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
    lb=$(grep "^LOCKED_BY:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
    la=$(grep "^LOCKED_AT:" "$tf" 2>/dev/null | cut -d: -f2- | tr -d ' ')
    [ "$s" = "active" ] && [ -n "$lb" ] && [ -n "$la" ] || continue
    le=$(date -d "$la" +%s 2>/dev/null || echo 0)
    age=$(( ($(date +%s) - le) / 60 ))
    if [ "$age" -gt 60 ] && [ "$age" -lt 65 ]; then
        notify "⚠️ Stalled" "$(basename "$tf" .task) locked by ${lb} ${age}m" "high"
    fi
done
