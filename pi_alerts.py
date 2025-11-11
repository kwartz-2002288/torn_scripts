from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

DEBUG = True

# set_up
config = load_config()
torn_key = config["torn_keys"]["Kwartz"]
free_keys = config["free_keys"]
computer = config["computer"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

# get data from torn API
# properties_info = safe_get(
#     f"https://api.torn.com/user/?selections=properties&key={torn_key}"
#     )["properties"]
properties_info = safe_get(
    f"https://api.torn.com/v2/user/properties?filters=ownedByUser"
    f"&offset=0&limit=20&key={torn_key}"
    )["properties"]
#raise SystemExit("Manual stop.")

# property alert limit
days_alert_limit = 4
not_rented = 0

# Prepare the message
all_good = True
sms_message = (
    f"ALERT from Torn Properties\n"
    f"report by {computer}\n"
)

for property_info in properties_info:

    if property_info["property"]["name"] == "Private Island": # select PI

        if property_info["status"] == "rented": # PI is rented
            days_left = property_info["rental_period_remaining"]
            if days_left < days_alert_limit:
                all_good = False
                tenant = property_info["used_by"][0]["name"]
                sms_message += f"PI lease ending in {days_left} days\n"
                sms_message += f"tenant: {tenant}\n"
        else: # PI is not rented
            all_good = False
            not_rented += 1

if all_good:
    sms_message += "All good!"
else:
    if not_rented > 0:
        sms_message += f"{not_rented} PI not rented\n"

sms_status = send_sms(message = sms_message, api_keys = free_keys)

if DEBUG:
    print(sms_message)
    print(f"SMS sending report: {sms_status}")