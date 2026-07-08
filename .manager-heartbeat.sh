#!/bin/bash
# Manager Heartbeat — runs every 30min
# Silent monitor: checks GitHub pipeline, flags stalls, does NOT write noise to TEAM_COMMS.md

set -euo pipefail
export PATH="/usr/bin:/bin:/usr/local/bin"

SID_DIR="/root/SID-OS"
LOG="/tmp/sid-manager-beat.log"
COMMS="${SID_DIR}/TEAM_COMMS.md"
GH_REPO="Ryuupyroxi/SID-OS"
NOW=$(date -u '+%Y-%m-%d %H:%M UTC')
BEAT=$(date +%s)

# Source token
export GH_TOKEN="$(cat /root/.sid-token 2>/dev/null | grep GH_TOKEN | cut -d= -f2- | tr -d '"' || true)"
export GH_PROMPT_DISABLED=1

log() { echo "[${NOW}] $*" >> "$LOG"; }
beat_secs() { echo $(( $(date +%s) - BEAT )); }

log "=== MANAGER BEAT ==="

cd "$SID_DIR" 2>/dev/null || { log "FAIL: cd"; exit 1; }

# 1. Quick git sync
git fetch origin 2>/dev/null

# 2. Check open issues (stalled = unassigned > 2hr)
STALLED=$(gh issue list --repo "$GH_REPO" --state open --json number,title,updatedAt,assignees 2>/dev/null | python3 -c "
import json,sys,datetime
now=datetime.datetime.now(datetime.timezone.utc)
try:
    for i in json.load(sys.stdin):
        age=now-datetime.datetime.fromisoformat(i['updatedAt'].replace('Z','+00:00'))
        if age.total_seconds()>7200 and not i.get('assignees'):
            print(f'#{i[\"number\"]}: {i[\"title\"][:60]}')
except: pass
" 2>/dev/null)
if [ -n "$STALLED" ]; then
    log "STALLED:"
    echo "$STALLED" | while read -r l; do log "  $l"; done
fi

# 3. Check mergeable PRs with no reviews
READY=$(gh pr list --repo "$GH_REPO" --state open --json number,title,mergeable,reviews,additions,deletions 2>/dev/null | python3 -c "
import json,sys
try:
    for p in json.load(sys.stdin):
        if p.get('mergeable')=='MERGEABLE' and not (p.get('reviews') or []):
            print(f'PR#{p[\"number\"]}: {p[\"title\"][:60]}')
except: pass
" 2>/dev/null)
if [ -n "$READY" ]; then
    log "READY-TO-MERGE:"
    echo "$READY" | while read -r l; do log "  $l"; done
fi

# 4. Check for Manager-direct messages in TEAM_COMMS.md
if [ -f "$COMMS" ]; then
    MSGS=$(awk '/From:.*→ Manager/{p=1} p{print; if(/^---/){p=0}}' "$COMMS" 2>/dev/null | grep -c "Status:" || true)
    [ "$MSGS" -gt 0 ] && log "Messages for Manager: $MSGS"
fi

log "Beat complete ($(beat_secs)s)"
