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

# get properties information
properties_info = safe_get(
    f"https://api.torn.com/v2/user/properties?filters=ownedByUser"
    f"&offset=0&limit=20&key={torn_key}"
    )["properties"]

# property alert limit
days_alert_limit = 4
not_rented = 0
for_rent = 0

# Prepare the message
all_good = True
sms_message = (
    f"ALERT about Torn Properties\n"
)

for property_info in properties_info:

    if property_info["property"]["name"] == "Private Island": # select PI only

        if property_info["status"] == "rented": # PI is rented
            days_left = property_info["rental_period_remaining"]
            if days_left < days_alert_limit:
                all_good = False
                tenant = property_info["used_by"][0]["name"]
                sms_message += f"PI lease ending in {days_left} days\n"
                sms_message += f"tenant: {tenant}\n"
        else: # PI is not rented
            all_good = False
            if property_info["status"] =="none":
                not_rented += 1
            elif property_info["status"] == "for_rent":
                for_rent += 1
                cost_per_day = str(int(property_info["cost_per_day"]/1000))
                rental_period = property_info["rental_period"]
                sms_message += (f"PI on rental market:\n"
                                f"   {rental_period} days, {cost_per_day} k$/day"
                                f"\n")

if all_good:
    sms_message += "All good!"
else:
    total_problems = not_rented + for_rent
    if for_rent > 0:
        sms_message += f"{for_rent} PI(s) on rental market\n"
    if not_rented > 0:
        sms_message += f"{not_rented} PI(s) not rented\n"
    sms_message += f"total: {total_problems} problems \n"

sms_message += f"report by {computer}\n"

sms_status = send_sms(message = sms_message, api_keys = free_keys)

if DEBUG:
    print(sms_message)
    print(f"SMS sending report: {sms_status}")