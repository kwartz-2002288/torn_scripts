import os
import time
import platform
from datetime import datetime, timedelta, timezone

def schedule_task(scripts_path: str, delay_seconds: int, label: str):
    """Schedule a script to run after a delay using 'at' (Linux) or 'sleep' (macOS)."""
    system = platform.system()
    delay_seconds = int(round(delay_seconds))
    now_date = datetime.now(timezone.utc)
    now = now_date.strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"Scheduling '{label}' in {delay_seconds} seconds (at {now_date + timedelta(seconds=delay_seconds)} UTC)")

    if system == "Linux":
        # Build the command for 'at'
        run_time = (now_date + timedelta(seconds=delay_seconds)).strftime('%H:%M %Y-%m-%d')
        at_command = f'echo "python3 {scripts_path} {label}" | at -t {run_time.replace("-", "").replace(":", "").replace(" ", "")}'
        os.system(at_command)

    elif system == "Darwin":  # macOS
        # Use sleep and os.fork (non-blocking)
        pid = os.fork()
        if pid == 0:
            time.sleep(delay_seconds)
            os.system(f'python3 {scripts_path} {label}')
            os._exit(0)
    else:
        raise Exception(f"Unsupported system: {system}")

# --- Simulated cooldowns in seconds ---
cooldowns = {
    "drug": 6 * 3600 + 15,   # 6h15
    "nerve": 3 * 3600 + 30,  # 3h30
    "happy": 5 * 3600        # 5h00
}

# Fake script to call — could be replaced with your real one
script_to_call = "/path/to/notify_cooldown.py"

# Loop over each cooldown type and schedule the task
for label, delay in cooldowns.items():
    schedule_task(script_to_call, delay, label)
