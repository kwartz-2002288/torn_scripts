from datetime import datetime, timezone
from jpr_lib import load_config, send_sms, safe_get

DEBUG = False

# set_up
config = load_config()
torn_key = config["torn_keys"]["Kwartz"]
free_keys = config["free_keys"]
computer = config["computer"]

# get data from torn API
company_employees = safe_get(f"https://api.torn.com/company/?selections=employees&key={torn_key}")[
    "company_employees"]
company_detailed = safe_get(f"https://api.torn.com/company/?selections=detailed&key={torn_key}")[
    "company_detailed"]
company = safe_get(f"https://api.torn.com/company/?selections=profile&key={torn_key}")["company"]

# script execution start schedule
now_date = datetime.now(timezone.utc)
now_date_str = now_date.strftime("%Y/%m/%d %H:%M:%S UTC")

# company alerts limits
trains_alert_limit = 10
hours_to_evaluation_limit = 24

# company evaluation schedule
evaluation_time = now_date.replace(hour=18, minute=0)

# delta hours to evaluation_time
delta_hours_to_evaluation = (evaluation_time - now_date).total_seconds() / 3600

trains_available = company_detailed["trains_available"]
popularity = company_detailed["popularity"]

employees_hired = company["employees_hired"]
employees_capacity = company["employees_capacity"]
rating = company["rating"]

# Prepare the message
all_good = True
sms_message = (
    f"NNN {rating}* network company\n"
    f"report by {computer}\n"
)

# Compute delta time and determine before or after
before_after = "before" if delta_hours_to_evaluation > 0 else "after"
delta_hours_to_evaluation = abs(delta_hours_to_evaluation)

if delta_hours_to_evaluation > 1:
    sms_message += f"{round(delta_hours_to_evaluation)} h {before_after} evaluation\n"
else:
    sms_message += f"{round(delta_hours_to_evaluation * 60)} m {before_after} evaluation\n"

# alert if staff incomplete
if employees_hired < employees_capacity:
    all_good = False
    sms_message += f"ALERT! {employees_hired}/{employees_capacity} hired\n"

#test trains available and alert if too high
if trains_available > trains_alert_limit:
    all_good = False
    sms_message += f"ALERT! {trains_available} trains available\n"

activity_message = ""
good_activity = True

for employee_id, employee in company_employees.items():
    # employee data
    name = employee["name"]
    position = employee["position"]
    wage = employee["wage"]
    merits = employee["effectiveness"].get("merits", 0)
    inactivity = employee["effectiveness"].get("inactivity", 0)
    # afk analysis
    timestamp = employee["last_action"]["timestamp"]
    employee_last_action_date = datetime.fromtimestamp(timestamp, timezone.utc)
    afk_duration = now_date - employee_last_action_date
    afk_days = afk_duration.days
    afk_hours = afk_duration.seconds / 3600
    afk_hours_at_evaluation = afk_days * 24 + afk_hours + delta_hours_to_evaluation
    if afk_hours_at_evaluation > hours_to_evaluation_limit:
        good_activity = False
        afk_days_at_evaluation, afk_hours_remainder = divmod(afk_hours_at_evaluation, 24)
        activity_message += f"{name}: "
        if afk_days_at_evaluation > 0:
            activity_message += f"{int(afk_days_at_evaluation)}d "
        activity_message += f"{afk_hours_remainder:.1f}h\n"

if not good_activity:
    activity_message = "Employee inactivity:\n" + activity_message
    sms_message += activity_message

if all_good and good_activity:
    sms_message += "All good"

sms_status = send_sms(message = sms_message, api_keys = free_keys)

if DEBUG:
    print(sms_message)
    print(f"SMS sending report: {sms_status}")
