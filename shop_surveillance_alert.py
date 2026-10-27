from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

# Set up
config = load_config()
runtime_data = config["runtime_data"]
computer = config["computer"]

torn_key = runtime_data["torn_keys"]["Kwartz"]
sms_account = runtime_data["sms_account"]

# Set to True to simulate alert conditions for all monitored shops.
TEST_MODE = False

# Script execution time
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

# Shops to monitor.
# Only the listed surveillance devices need to be disabled for an alert.
shops_to_monitor = {
    22: {
        "name": "Super Store",
        "required_disabled": {"Two cameras"},
        "items": ["Receipt", "Voice Recorder"],
    },
    24: {
        "name": "Jewelry Store",
        "required_disabled": {"Three cameras", "One guard"},
        "items": ["Cluster Ring"],
    },
}

shoplifting = safe_get(
    url="https://api.torn.com/v2/torn/shoplifting",
    torn_key=torn_key,
)["shoplifting"]

shops_by_id = {shop["id"]: shop for shop in shoplifting}

for shop_id, alert_config in shops_to_monitor.items():
    shop = shops_by_id.get(shop_id)
    if shop is None:
        print(f"Shoplifting surveillance id {shop_id} not found in API response")
        continue

    devices = shop["status"]
    disabled_devices = {
        device["title"]
        for device in devices
        if device["disabled"]
    }

    if TEST_MODE:
        if shop_id == 22: #22
            disabled_devices = {"Two cameras"}
        elif shop_id == 24: #24
            disabled_devices = {"Three cameras", "One guard"}

    if alert_config["required_disabled"].issubset(disabled_devices):
        sms_message = (
            f"{now_date_str}\n"
            f"{alert_config['name']}\n"
            f"Surveillance Disabled:\n"
            f"{', '.join(sorted(alert_config['required_disabled']))}\n"
            f"{'Unique' if len(alert_config['items']) == 1 else 'Uniques'}: "
            f"{', '.join(alert_config['items'])}\n"
            f"Report by {computer}\n"
        )

        send_sms(message=sms_message, sms_account=sms_account)
        print(sms_message)
        print(devices)
