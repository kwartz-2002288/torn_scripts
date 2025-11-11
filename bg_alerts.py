from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

DEBUG = False

# set_up
config = load_config()
torn_key = config["torn_keys"]["Kwartz"]
free_keys = config["free_keys"]
computer = config["computer"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

# get Nikeh shop inventory
id_Nikeh = "111"
id_Boxing_Gloves = "330"

Nikeh_shop_inventory = safe_get(
    f" https://api.torn.com/torn/?selections=cityshops&key={torn_key}"
    )["cityshops"][id_Nikeh]["inventory"]

if DEBUG:
    print(Nikeh_shop_inventory)

# Prepare the message
all_good = True
sms_message = (
    f"ALERT from Nikeh Shop\n"
    f"report by {computer}\n"
)
if id_Boxing_Gloves in Nikeh_shop_inventory:
    N_items = Nikeh_shop_inventory[id_Boxing_Gloves]["in_stock"]
    sms_message += f"{N_items} boxing gloves here!"

    if DEBUG:
        print(sms_message)
    sms_status = send_sms(message=sms_message, api_keys=free_keys)
    if DEBUG:
        print(sms_status)
else:
    if DEBUG:
        print("No boxing gloves available.")

