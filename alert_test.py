from jpr_lib import load_config, send_sms, safe_get

# set_up
config = load_config()
torn_key = config["torn_keys"]["Kwartz"]
free_keys = config["free_keys"]

# Get data from torn API
jewelry_store_status = safe_get(f"https://api.torn.com/torn/?selections=shoplifting&key={torn_key}")["shoplifting"]["jewelry_store"]
print(jewelry_store_status)
status = []
if all(item['disabled'] for item in jewelry_store_status):
    print("ALL DISABLED")
else:
    print("SURVEILLANCE ON")
raise SystemExit("Fin du test")

# Prepare the message
sms_message = (
    f"Jewelry surveillance status\n")

# [{'title': 'Three cameras', 'disabled': False}, {'title': 'One guard', 'disabled': False}]
check = send_sms(message=sms_message, api_keys=free_keys)
print(f"SMS sending report: {check}")
