#!/usr/bin/env bash
# DKF WSN Cycle Launcher with flock deduplication
REPO_DIR="/home/sim/DKF_WSN_Experiment"
PYTHON_BIN="/home/sim/alpaca_env/bin/python3"
LOCK_FILE="$REPO_DIR/experiment.lock"

cd "$REPO_DIR" || exit 1

# Ensure non-overlapping execution using flock
exec 9> "$LOCK_FILE"
if ! flock -n 9; then
    echo "[$(date)] DKF WSN cycle already running. Skipping."
    exit 0
fi

echo "[$(date)] Starting DKF WSN automated simulation & optimization cycle..."

# Run full experiments
"$PYTHON_BIN" run_experiments.py >> "$REPO_DIR/cron_run.log" 2>&1

# Run self-improving optimizer
"$PYTHON_BIN" auto_optimizer.py >> "$REPO_DIR/cron_optimizer.log" 2>&1

echo "[$(date)] DKF WSN cycle completed successfully."
