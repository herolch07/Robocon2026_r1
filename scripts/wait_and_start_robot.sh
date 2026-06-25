#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="${R1_TMUX_SESSION:-r1_control}"
START_SCRIPT="${R1_START_SCRIPT:-$WS_DIR/r1_start_base_1_0.sh}"
CHECK_INTERVAL_SEC="${CHECK_INTERVAL_SEC:-1}"
DEVICE_NAME_FILTER="${DEVICE_NAME_FILTER:-8BitDo}"
STOP_ON_CONTROLLER_LOST="${STOP_ON_CONTROLLER_LOST:-0}"
CONTROLLER_DEVICE="${CONTROLLER_DEVICE:-}"

log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

tmux_running() {
    tmux has-session -t "$SESSION" 2>/dev/null
}

controller_active() {
    if [ -n "$CONTROLLER_DEVICE" ] && [ -e "$CONTROLLER_DEVICE" ]; then
        return 0
    fi

    python3 - "$DEVICE_NAME_FILTER" <<'PY_INNER'
import sys

try:
    from evdev import InputDevice, list_devices
except Exception:
    sys.exit(2)

name_filter = sys.argv[1]
supported = {
    "8BitDo Ultimate Wireless / Pro 2 Wired Controller",
    "Generic X-Box pad",
}

for path in list_devices():
    try:
        device = InputDevice(path)
    except Exception:
        continue
    name = device.name or ""
    if name in supported or (name_filter and name_filter in name):
        sys.exit(0)

sys.exit(1)
PY_INNER
}

start_robot() {
    if tmux_running; then
        log "tmux session '$SESSION' already running; not starting again"
        return
    fi

    if [ ! -x "$START_SCRIPT" ]; then
        log "start script is not executable: $START_SCRIPT"
        return
    fi

    log "controller active; starting robot system"
    R1_NO_TMUX_ATTACH=1 "$START_SCRIPT"
}

stop_robot_if_configured() {
    if [ "$STOP_ON_CONTROLLER_LOST" != "1" ]; then
        return
    fi
    if tmux_running; then
        log "controller lost; stopping tmux session '$SESSION'"
        tmux kill-session -t "$SESSION"
    fi
}

log "R1 autostart watcher started"
log "workspace: $WS_DIR"
log "session: $SESSION"
log "device filter: $DEVICE_NAME_FILTER"
log "stop on controller lost: $STOP_ON_CONTROLLER_LOST"

while true; do
    if controller_active; then
        start_robot
    else
        log "waiting for controller..."
        stop_robot_if_configured
    fi
    sleep "$CHECK_INTERVAL_SEC"
done
