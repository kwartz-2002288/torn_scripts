from jpr_lib import load_config, send_sms, safe_get
from datetime import datetime

DEBUG = False

# set_up
config = load_config()
torn_key = config["torn_keys"]["Kwartz"]
free_keys = config["free_keys"]
computer = config["computer"]

# Get current local time as string
current_time = datetime.now().strftime("%d-%b %H:%M:%S")

# Get surveillance data from torn API v1
# Shop names:
# "sallys_sweet_shop","Bits_n_bobs","tc_clothing","super_store",
# "cyber_force","pharmacy","big_als","jewelry_store"
#
# "jewelry_store": [
#     {
#         "title": "Three cameras",
#         "disabled": false,
#     },
#     {
#         "title": "One guard",
#         "disabled": false,
#     },
# ]

shop = "jewelry_store"
devices = safe_get(
    f"https://api.torn.com/torn/"
    f"?selections=shoplifting&key={torn_key}"
)["shoplifting"][shop]

# Detect disabled surveillance
disabled_devices = [d['title'] for d in devices if d['disabled']]

if DEBUG:
    print(devices)

# Prepare the message with execution time
sms_message = (
    f"{shop} surveillance\n"
    f"report by {computer}\n"
    f"{current_time}\n"
)
# Send SMS only if all devices are disabled
if len(disabled_devices) == len(devices):
    sms_message += (f"SURVEILLANCE DISABLED:\n"
                    f"{', '.join(disabled_devices)}\n")
    sms_status = send_sms(message=sms_message, api_keys=free_keys)
    if DEBUG:
        print(sms_message)
        print(f"SMS sending report: {sms_status}")




