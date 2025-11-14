from jpr_lib import load_config, safe_get, python_date_to_excel_number
import gspread
from datetime import datetime, timezone

def update_gym ( name , gc, spreadsheet_id, torn_keys, the_row ):

# Get data from TORN in r (dict)
    torn_key = torn_keys[name]
    r=safe_get(f'https://api.torn.com/user/?'
                       f'selections=battlestats&key={torn_key}')
# Open the Google sheet (don't forget to share it with the gspread mail address)
###   projettorn@appspot.gserviceaccount.com   ###
    ws = gc.open_by_key(spreadsheet_id).worksheet('Gym')

# Get stats, convert in millions and update sheet

    buffer = [name]
    for the_stat in ['dexterity','defense','speed','strength']:
            buffer.append(int(float(r[the_stat])))
    zone_to_be_filled = "A" + the_row + ":E" + the_row
    ws.update(range_name=zone_to_be_filled, values=[buffer])
    return

def main():
    config = load_config()
    torn_keys = config['torn_keys']
    json_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["torn_stats"]
    computer_name = config.get("computer", "unknown")
    gc = gspread.service_account(filename=json_keyfile)

    date_now = datetime.now(timezone.utc)
    #current_date_str = date_now.strftime("%d/%m/%Y %H:%M:%S")
    current_date_num = python_date_to_excel_number(date_now)
    update_gym( "Kivou" , gc, spreadsheet_id, torn_keys, "1")
    update_gym( "Kwartz" , gc, spreadsheet_id, torn_keys, "2")
    # Write the date
    ws = gc.open_by_key(spreadsheet_id).worksheet('Gym')
    ws.update_cell(3, 1, "Updated by " + computer_name)
    ws.update_cell(3, 2, current_date_num)

if __name__ == "__main__":
    main()