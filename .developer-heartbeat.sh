#!/bin/bash
# Developer Heartbeat — runs every 30 minutes (managed by Manager)
# Developer: designs new features, refines applications, conceptualizes OS improvements.
# Automated architectural heartbeat — checks for design requests and review needs.

set -euo pipefail
export PATH="/usr/bin:/bin:/usr/local/bin"

SID_DIR="/root/SID-OS"
LOG="/tmp/sid-developer-beat.log"
COMMS="${SID_DIR}/TEAM_COMMS.md"
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

# 3. Check TEAM_COMMS.md for Developer-directed messages
if [ -f "$COMMS" ]; then
    MSGS=$(awk '/→ Developer/{p=1} p{print; if(/^---/){p=0}}' "$COMMS" 2>/dev/null | grep -c "Status:" || true)
    [ "$MSGS" -gt 0 ] && log "Messages for Developer: $MSGS"
fi

log "Beat complete"
