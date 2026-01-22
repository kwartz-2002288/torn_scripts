from datetime import datetime, timezone
from pprint import pprint
from jpr_lib import load_config, send_sms, safe_get

DEBUG = False

# set_up
config = load_config()
runtime_data = config["runtime_data"]
computer = config["computer"]

torn_key = runtime_data["torn_keys"]["Kwartz"]
sms_account = runtime_data["sms_account"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

# get properties information
properties_info = safe_get(
    url = f"https://api.torn.com/v2/user/properties?filters=ownedByUser&offset=0&limit=20",
    torn_key = torn_key
    )["properties"]

if DEBUG:
    pprint(properties_info)

# property alert limit
days_alert_limit = 4
not_rented = 0
for_rent = 0

# Prepare the message
all_good = True
msg_lines = ["ALERT about Torn Properties"]

for property_info in properties_info:
    if property_info["property"]["name"] in {"Private Island"}: # select PI only

        if property_info["status"] == "rented": # PI is rented
            days_left = property_info["rental_period_remaining"]
            if days_left < days_alert_limit:
                all_good = False
                tenant = property_info["rented_by"]["name"]
                msg_lines.append(f"PI lease ending in {days_left} days")
                msg_lines.append(f"tenant: {tenant}")

        else: # PI is not rented
            all_good = False
            if property_info["status"] =="none":
                not_rented += 1
            elif property_info["status"] == "for_rent":
                for_rent += 1
                cost_per_day = str(int(property_info["cost_per_day"]/1000))
                rental_period = property_info["rental_period"]
                msg_lines.append(f"PI on rental market:")
                msg_lines.append(f"   {rental_period} days, {cost_per_day} k$/day")

if all_good:
    msg_lines.append("All good!")
    sms_status = "SMS not sent"
    sms_message = "\n".join(msg_lines)
else:
    total_problems = not_rented + for_rent
    if for_rent:
        msg_lines.append(f"{for_rent} PI(s) on rental market")
    if not_rented:
        msg_lines.append(f"{not_rented} PI(s) not rented")
    if for_rent or not_rented:
        msg_lines.append(f"total: {total_problems} problem(s)")
    msg_lines.append(f"Report by {computer}")

    sms_message = "\n".join(msg_lines)
    sms_status = send_sms(message=sms_message, sms_account=sms_account)

if DEBUG:
    print(sms_message)
    print(f"SMS sending report: {sms_status}")