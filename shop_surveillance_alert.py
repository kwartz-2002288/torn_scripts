from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

DEBUG = True

# set_up
config = load_config()
runtime_data = config["runtime_data"]
computer = config["computer"]

torn_key = runtime_data["torn_keys"]["Kwartz"]
sms_account = runtime_data["sms_account"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

shop = "jewelry_store"
# NOTE: The shop IDs in `shoplifting` have changed and are inconsistent with those in `cityshops`.
shop_id = 24

shoplifting = safe_get(
    url="https://api.torn.com/v2/torn/shoplifting",
    torn_key=torn_key
)["shoplifting"]

devices = next(
    shop for shop in shoplifting
    if shop["id"] == shop_id
)["status"]

# Detect disabled surveillance
disabled_devices = [d['title'] for d in devices if d['disabled']]

# Prepare the message with execution time
sms_message = (
    f"{shop} surveillance\n"
    f"{now_date_str}\n"
)
# Send SMS only if all devices are disabled
if len(disabled_devices) == len(devices):
    sms_message += (f"SURVEILLANCE DISABLED:\n"
                    f"{', '.join(disabled_devices)}\n")
    sms_message += f"Report by {computer}\n"
    sms_status = send_sms(message=sms_message, sms_account=sms_account)
if DEBUG:
    print(sms_message)
    print(devices)




