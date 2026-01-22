from jpr_lib import load_config, safe_get, datetime_to_excel_date
from datetime import datetime, timezone
import gspread

def update_gym(ws, name: str, torn_keys: dict, the_row: str):
    """
    Update a row in the Gym sheet for a given user.
    """
    torn_key = torn_keys[name]

    # Get battle stats
    battle_stats = safe_get(
        url=f"https://api.torn.com/v2/user/personalstats?cat=battle_stats",
        torn_key=torn_key
        )["personalstats"]["battle_stats"]

    # Prepare values
    stats_values = [battle_stats[stat] for stat in ['dexterity', 'defense', 'speed', 'strength']]
    buffer = [name] + stats_values
    zone_to_be_filled = f"A{the_row}:E{the_row}"

    # Update the worksheet
    ws.update(range_name=zone_to_be_filled, values=[buffer])


def main():
    # Load configuration
    config = load_config()
    runtime_data = config["runtime_data"]
    service_file = config["data_path"] + runtime_data["google"]["service_account_file"]
    computer = config["computer"]

    torn_keys = runtime_data["torn_keys"]
    spreadsheet_id = runtime_data["spreadsheet_ids"]["torn_stats"]

    # Connect to Google Sheets
    gs_client = gspread.service_account(filename=service_file) #
    spreadsheet = gs_client.open_by_key(spreadsheet_id)
    ws_gym = spreadsheet.worksheet('Gym')

    # Update users
    update_gym(ws_gym, "Kivou", torn_keys, "1")
    update_gym(ws_gym, "Kwartz", torn_keys, "2")

    # Update timestamp
    current_date_num = datetime_to_excel_date(datetime.now(timezone.utc))
    ws_gym.update_cell(3, 1, f"Updated by {computer}")
    ws_gym.update_cell(3, 2, current_date_num)

# updated with runtime_data
if __name__ == "__main__":
    main()
