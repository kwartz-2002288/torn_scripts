import json
import os
from jpr_lib import load_config, safe_get
import gspread, re
from datetime import datetime, timezone

DEBUG = True

def extract_destination(description):
    desc = description.strip()
    if desc.startswith("In a "):
        dest = desc[5:].split(" for ")[0]
    elif desc.startswith("In "):
        dest = desc[3:]
    elif desc.startswith("Traveling to "):
        dest = desc[12:]
    elif desc.lower().startswith("returning to torn from "):
        dest = "zzz_" + desc[24:]
    else:
        dest = "zzz"
    return dest.strip()


foreign_hospital_pattern = re.compile(r"^In (a|an) .+ hospital", re.IGNORECASE)

def get_priority_status(description):
    desc_lower = description.lower()

    if description.startswith("In ") and not "hospital" in desc_lower:
        return 1
    elif foreign_hospital_pattern.match(description):
        return 2
    elif description.startswith("Traveling to "):
        return 3
    elif desc_lower.startswith("returning to torn from "):
        return 4
    else:
        return 5


def load_state(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f)


def format_duration(seconds):
    minutes = seconds // 60
    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    minutes = minutes % 60
    if hours < 24:
        return f"{hours}h {minutes}m ago"
    days = hours // 24
    hours = hours % 24
    return f"{days}d {hours}h ago"


def filter_members(members, state_path):
    filtered = []

    # Load previous state
    prev_state = load_state(state_path)
    new_state = {}
    now = datetime.now(timezone.utc).timestamp()

    for member_id, info in members.items():
        desc = info.get("status", {}).get("description", "")
        desc_lower = desc.lower()

        # Filter conditions :
        if desc.startswith("In ") and "hospital" not in desc_lower:
            pass  # abroad (non-hospital)
        elif foreign_hospital_pattern.match(desc):
            pass  # abroad hospital (a/an ... hospital)
        elif desc.startswith("Traveling to "):
            pass
        elif desc.startswith("Returning to Torn from "):
            pass
        else:
            continue  # others ignored

        destination = extract_destination(desc)
        priority = get_priority_status(desc)

        # Check timestamp from previous state
        prev = prev_state.get(member_id)
        if prev and prev.get("description") == desc:
            timestamp = prev["timestamp"]
        else:
            timestamp = now  # new or changed

        duration = format_duration(int(now - timestamp))
        new_state[member_id] = {"description": desc, "timestamp": timestamp}

        filtered.append({
            "id": member_id,
            "name": info.get("name", ""),
            "level": info.get("level", 0),
            "status": desc,
            "link": f"https://www.torn.com/profiles.php?XID={member_id}",
            "destination": destination,
            "priority_status": priority,
            "since": duration,
        })

    # Save updated state
    save_state(state_path, new_state)

    # Sort
    filtered.sort(key=lambda x: (
        x["destination"].lower(),
        x["priority_status"],
        x["name"].lower()
    ))

    return filtered


def write_to_sheet(gc, spreadsheet_id, sheet_name, computer_name, filtered):
    try:
        worksheet = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = gc.open_by_key(spreadsheet_id).add_worksheet(title=sheet_name, rows=1000, cols=10)

    worksheet.clear()

    utcnow_str = datetime.now(timezone.utc).strftime("%d-%b-%y at %H:%M UTC")

    worksheet.update([[f"updated by {computer_name} (kwartz)"]], "B1")
    worksheet.update([[utcnow_str]], "B2")
    worksheet.update([["members abroad or travelling"]], "E1")
    worksheet.update([[f"{len(filtered)}"]], "E2")

    values = [["ID", "Name", "Level", "Status", "Link", "Since"]]
    for row in filtered:
        values.append([row["id"], row["name"], row["level"], row["status"], row["link"], row["since"]])

    worksheet.update(values, "A3")


def main():
    config = load_config()
    torn_key = config["torn_keys"]["Kwartz"]
    data_path_abroad = config["data_path"] + "abroad/"
    json_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["abroad_targets"]
    computer_name = config.get("computer", "unknown")

    gc = gspread.service_account(filename=json_keyfile)

    with open(data_path_abroad + "factions_abroad.json", 'r') as f:
        faction_list = json.load(f)

    for faction_id in faction_list:
        if DEBUG:
            print(f"Fetching data for faction {faction_id}...")

        url = f"https://api.torn.com/faction/{faction_id}?selections=&key={torn_key}"
        data = safe_get(url)
        members = data.get("members", {})
        tag = data.get("tag", f"faction_{faction_id}")

        state_path = os.path.join(data_path_abroad, f"abroad_state_{faction_id}.json")

        filtered = filter_members(members, state_path)
        write_to_sheet(gc, spreadsheet_id, tag, computer_name, filtered)
        if DEBUG:
            print(f"{len(filtered)} members written to tab '{tag}'.")


if __name__ == "__main__":
    main()
