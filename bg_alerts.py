from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

# set_up
config = load_config()
runtime_data = config["runtime_data"]
computer = config["computer"]

torn_key = runtime_data["torn_keys"]["Kwartz"]
sms_account = runtime_data["sms_account"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S UTC")

# get Nikeh shop inventory
id_Nikeh = "111"
id_Boxing_Gloves = "330"

Nikeh_shop_inventory = safe_get(
    f" https://api.torn.com/torn/?selections=cityshops&key={torn_key}"
    )["cityshops"][id_Nikeh]["inventory"]

# Prepare the message
all_good = True
lines = ["ALERT from Nikeh Shop"]

if id_Boxing_Gloves in Nikeh_shop_inventory:
    N_items = Nikeh_shop_inventory[id_Boxing_Gloves]["in_stock"]
    lines.append(f"{N_items} boxing gloves here!")
    lines.append(f"report by {computer}")
    sms_message = "\n".join(lines)

    sms_status = send_sms(message = sms_message, sms_account = sms_account)



