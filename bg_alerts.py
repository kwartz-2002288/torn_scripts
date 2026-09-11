from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

import logging
# configure logging for cron (only needed for warnings/errors)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# set_up
config = load_config()
runtime_data = config["runtime_data"]
computer = config["computer"]

torn_key = runtime_data["torn_keys"]["Kwartz"]
sms_account = runtime_data["sms_account"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

# get shops inventory

data = safe_get(
    "https://api.torn.com/v2/torn/cityshops",
    torn_key=torn_key
)

# select shop and item
shop_name = "Nikeh Performance"
item_name = "Boxing Gloves"

shop = next(
    shop for shop in data["cityshops"]
    if shop["name"] == shop_name
)

item = next(
    item for item in shop["items"]
    if item["name"] == item_name
)

n_items = item["stock"]["current"]

# Prepare the message
if n_items > 0:
    msg_lines = ["ALERT from Nikeh Shop"]
    msg_lines.append(f"{n_items} boxing gloves here!")
    msg_lines.append(f"Report by {computer}")
    sms_message = "\n".join(msg_lines)

    if not send_sms(message=sms_message, sms_account=sms_account):
        logging.error(
            "Alert SMS failed in bg_alerts| time=%s",
            now_date_str
        )