#!/usr/bin/env bash
# Status script for DKF WSN Experiment Pipeline
REPO_DIR="/home/sim/DKF_WSN_Experiment"

echo "=== DKF WSN EXPERIMENT PIPELINE STATUS ==="
echo "1. Process check:"
pgrep -af "run_experiments.py" || echo "  No active simulation process."

echo -e "\n2. Lock status check:"
if flock -n "$REPO_DIR/experiment.lock" -c "true"; then
    echo "  Lock is FREE (no cycle currently running)."
else
    echo "  Lock is HELD (cycle currently running)."
fi

echo -e "\n3. Optimized configuration summary:"
if [ -f "$REPO_DIR/optimized_config.json" ]; then
    cat "$REPO_DIR/optimized_config.json"
else
    echo "  No optimized config found yet."
fi

echo -e "\n4. Recent log output (tail cron_run.log):"
if [ -f "$REPO_DIR/cron_run.log" ]; then
    tail -n 5 "$REPO_DIR/cron_run.log"
else
    echo "  No cron_run.log found yet."
fi
