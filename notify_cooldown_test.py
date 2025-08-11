import sys
from datetime import datetime, timezone

label = sys.argv[1] if len(sys.argv) > 1 else "unknown"
now_date = datetime.now(timezone.utc)
now = now_date.strftime("%Y-%m-%d %H:%M:%S UTC")
print(f"[{now}] ⏰ Cooldown '{label}' expired! Time to act!")
