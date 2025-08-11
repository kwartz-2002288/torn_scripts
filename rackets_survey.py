import json
import os

from jpr_lib import load_config, safe_get
from datetime import datetime, timezone
import requests

def load_state(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f)

def load_factions(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
            raise FileNotFoundError(f"Required file not found: {path}")

def compare_dicts(prev_state: dict, new_state: dict):
    prev_keys = set(prev_state.keys())
    new_keys = set(new_state.keys())

    # Keys added
    added = new_keys - prev_keys

    # Keys removed
    removed = prev_keys - new_keys

    # Keys present in both, but with different content
    modified = {
        key for key in prev_keys & new_keys
        if prev_state[key] != new_state[key]
    }

    return {
        "added": added,
        "removed": removed,
        "modified": modified
    }

def main():
    config = load_config()
    torn_key = config["torn_keys"]["Kwartz"]
    data_path = config["data_path"]
    json_keyfile = data_path + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["abroad_targets"]
    computer_name = config.get("computer", "unknown")
    state_path = data_path + "rackets_state.json"
    factions_path = data_path + "faction_ids.json"

    # Load previous state
    prev_state = load_state(state_path)
    print(json.dumps(prev_state, indent=2))
    # load faction ids to check
    faction_ids = load_factions(factions_path)

    factions = {}
    for faction_id in faction_ids:
        url = f"https://api.torn.com/v2/faction/{faction_id}/basic?key={torn_key}"
        data = safe_get(url)["basic"]
        factions[faction_id] = {"name":data["name"], "tag": data["tag"]}

    url = f"https://api.torn.com/v2/faction/rackets?key={torn_key}"
    rackets_list = safe_get(url)["rackets"]

    # a racket state is a dictionary of dictionaries whose keys are racket territories
    # {"TRT1" : {"faction_id": integer, "name": string, etc...}

    new_state = {}
    for r in rackets_list:
        if r["faction_id"] in faction_ids:
            new_state[r["territory"]] = {
                "faction_id": r["faction_id"],
                "name": r["name"],
                "level": r["level"],
                "description": r["description"],
                "reward": r["reward"],
                "created_at": r["created_at"],
                "changed_at": r["changed_at"]
            }

    save_state(state_path, new_state)
    print(json.dumps(new_state, indent=2))

    result = compare_dicts(prev_state, new_state)
    print(f"comparison results: {result}")
#    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()