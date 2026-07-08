#!/bin/bash
# Coder Heartbeat — runs every 30 minutes (managed by Manager)
# Coder: implements code, references/closes issues via PRs. Automated ops heartbeat.

source /root/.sid-token 2>/dev/null
export GH_TOKEN="${GH_TOKEN:-}"
export SID_DIR="/root/SID-OS"
export WORKSPACE="/root/Documents/Codex/2026-07-01/what-all-are-you-capable-of"
export LOG="$WORKSPACE/heartbeat.log"
export TASK_LOCK="$WORKSPACE/.active-task"
TIME=$(date "+%Y-%m-%d %H:%M:%S")
BEAT=$(date "+%Y%m%d%H%M")

echo "[$TIME] === HEARTBEAT $BEAT ===" >> "$LOG"

cd "$SID_DIR" 2>/dev/null || { echo "  FAIL: cannot cd to $SID_DIR" >> "$LOG"; exit 1; }

# ── 1. Sync code ──
timeout 15 git fetch origin 2>/dev/null || true
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
echo "  Branch: $CURRENT_BRANCH @ $(git rev-parse HEAD | head -c 12)" >> "$LOG"

# Check for updates on current branch
BEHIND=$(git rev-list --count HEAD..origin/"$CURRENT_BRANCH" 2>/dev/null || echo 0)
if [ "$BEHIND" -gt 0 ]; then
    echo "  Behind origin by $BEHIND commits — pulling" >> "$LOG"
    git pull origin "$CURRENT_BRANCH" 2>/dev/null || true
fi

# ── 2. Check active task ──
ACTIVE_TASK=""
if [ -f "$TASK_LOCK" ]; then
    ACTIVE_TASK=$(cat "$TASK_LOCK" 2>/dev/null)
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$TASK_LOCK" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -gt 7200 ]; then
        echo "  Task lock stale ($((LOCK_AGE/60))m old), clearing" >> "$LOG"
        ACTIVE_TASK=""; rm -f "$TASK_LOCK"
    else
        echo "  Active: $ACTIVE_TASK ($((LOCK_AGE/60))m running)" >> "$LOG"
    fi
fi

# ── 3. Check /etc/sid/team/comms.md for teammate messages ──
cd "$SID_DIR"
TEAM_COMMS="/etc/sid/team/comms.md"
if [ -f "$TEAM_COMMS" ]; then
    # Get all messages not yet acknowledged by Developer
    NEW_FROM_DEBUGGER=$(awk '/From: Debugger/{p=1} p{print; if(/^$|^---/){p=0}}' "$TEAM_COMMS" 2>/dev/null | grep -c "Status: Open")
    NEW_FROM_CODER=$(awk '/From: Coder/{p=1} p{print; if(/^$|^---/){p=0}}' "$TEAM_COMMS" 2>/dev/null | grep -c "Status: Open\|Waiting on")
    if [ "$NEW_FROM_DEBUGGER" -gt 0 ] || [ "$NEW_FROM_CODER" -gt 0 ]; then
        echo "  ⚡ Teammate messages: Debugger($NEW_FROM_DEBUGGER) Coder($NEW_FROM_CODER)" >> "$LOG"
        # Extract subject lines for context
        awk '/From: Debugger|From: Coder/{flag=1} flag{print; if(/^---/){flag=0}}' "$TEAM_COMMS" 2>/dev/null | grep "Subject:" >> "$LOG"
    fi
    # Check for direct replies to Developer
    NEW_REPLIES=$(grep -A3 "From:.*→ Developer" "$TEAM_COMMS" 2>/dev/null | grep -c "Status:")
    [ "$NEW_REPLIES" -gt 0 ] && echo "  Replies to Developer: $NEW_REPLIES" >> "$LOG"
fi

# ── 4. Check PRs and Issues ──
if [ -n "$GH_TOKEN" ] && [ -z "$ACTIVE_TASK" ]; then
    # PR status
    PR_DATA=$(curl -s "https://api.github.com/repos/Ryuupyroxi/SID-OS/pulls?state=open&per_page=3" \
      -H "Authorization: token $GH_TOKEN" 2>/dev/null | python3 -c "
import json,sys
for p in json.load(sys.stdin):
    print(f\"PR#{p['number']}: {p['title'][:50]} [{p['state']}]")
" 2>/dev/null)
    [ -n "$PR_DATA" ] && echo "  PRs: $PR_DATA" >> "$LOG" || echo "  No open PRs" >> "$LOG"
    
    # Unresolved issues
    ISSUES=$(curl -s "https://api.github.com/repos/Ryuupyroxi/SID-OS/issues?state=open&labels=bug&per_page=5" \
      -H "Authorization: token $GH_TOKEN" 2>/dev/null | python3 -c "
import json,sys
for i in json.load(sys.stdin):
    if 'pull_request' not in i:
        print(f\"Issue#{i['number']}: {i['title'][:50]}")
" 2>/dev/null)
    [ -n "$ISSUES" ] && echo "  Open bugs: $ISSUES" >> "$LOG"
fi

# ── 5. Run hourly character gen if not busy ──
HOUR=$(date +%H)
if [ -z "$ACTIVE_TASK" ] && [ "$HOUR" != "00" ]; then
    # Only generate if not already generated this hour
    LAST_CHAR=$(tail -5 "$LOG" 2>/dev/null | grep "char-" | tail -1 | grep -o "char-[0-9]*" || echo "")
    EXPECTED="char-${HOUR}"
    if [ "$LAST_CHAR" != "$EXPECTED" ]; then
        echo "  Generating $EXPECTED..." >> "$LOG"
        DESCRIPTIONS=(
            "a friendly retro robot with blue eyes"
            "a cool cat with sunglasses and a hat"
            "a wise old wizard with a long beard"
            "a cheerful alien with three eyes"
            "a mysterious ninja with a red scarf"
            "a happy dog with floppy ears"
            "a cute fox with big ears"
            "a sleepy sloth hanging from a branch"
            "a brave knight with a shiny helmet"
            "a playful penguin in a bowtie"
            "a stern owl in a tweed vest"
            "a sarcastic raven on a typewriter"
        )
        IDX=$((HOUR % ${#DESCRIPTIONS[@]}))
        DESC="${DESCRIPTIONS[$IDX]}"
        python3 -c "
from src.terminal.assistant.charforge import CharForge
CharForge().create_from_description('$DESC', name='auto-$EXPECTED')
" >> "$LOG" 2>&1 && git add -A && git commit -m "auto char ${HOUR}:00" && git push origin "$CURRENT_BRANCH" 2>/dev/null
    fi
fi

# ── 6. Quick health check ──
python3 -c "
import sys; sys.path.insert(0, '$SID_DIR/src')
from terminal.assistant.charforge import CharForge
from terminal.assistant.character import list_characters
from terminal.assistant.renderer import detect_best_renderer
print(f'  Characters: {len(list_characters())}')
print(f'  Renderer: {detect_best_renderer()}')
" >> "$LOG"
