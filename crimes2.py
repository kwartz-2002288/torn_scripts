from jpr_lib import load_config, safe_get, python_date_to_excel_number
import gspread
from datetime import datetime, timezone

DEBUG = True

def parse_crimes(skill_data, criminal_record, current_date_num):

    # define the ordered field names
    skill_keys = ["bootlegging", "burglary", "card_skimming", "graffiti",
        "hustling", "pickpocketing", "search_for_cash", "shoplifting",
        "disposal", "cracking", "forgery", "scamming", "arson",
        "reviving", "hunting", "racing"]

    crime_keys = ["vandalism", "theft", "counterfeiting", "fraud",
        "illicitservices", "cybercrime", "extortion", "illegalproduction",
        "total"]

    # parse skills (default 0 if missing)
    skills = [float(skill_data.get(k, 0)) for k in skill_keys]

    # parse crimes (default 0 if missing)
    crimes = [criminal_record.get(k, 0) for k in crime_keys]

    # build header and data
    crimes2_header = ["date"] + skill_keys + crime_keys
    crimes2_data = [current_date_num] + skills + crimes

    return crimes2_data, crimes2_header


def write_to_sheet(gc, spreadsheet_id, sheet_name, computer_name, crimes2_data, crimes2_header):
    #writing in spreadsheets if total crimes has changed
    ws = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)
    old_total = ws.cell(2,1).value
    old_total = int(old_total.replace(",", "").replace(" ", ""))
    crime_total = crimes2_data[-1]
    #print(old_total, crime_total)
    # if old_total > 0 :
    if old_total < crime_total:
        ws.update_cell(1, 1, "Updated by " + computer_name)
        # update header
        zone_to_be_filled = "A4:Z4"
        ws.update(range_name=zone_to_be_filled, values=[crimes2_header])
        # update data
        current_row = ws.cell(1,3).value # last row that has already been written
        current_row = 1 + int(''.join(current_row.split())) #clean string and convert to int
        zone_to_be_filled = "A" + str(current_row) + ":Z" + str(current_row)
        ws.update(range_name=zone_to_be_filled, values=[crimes2_data])

def main():
    config = load_config()
    json_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["torn_stats"]
    computer_name = config.get("computer", "unknown")
    gc = gspread.service_account(filename=json_keyfile)

    date_now = datetime.now(timezone.utc)
    #current_date_str = date_now.strftime("%d/%m/%Y %H:%M:%S")
    current_date_num = python_date_to_excel_number(date_now)

    for player_name in ('Kwartz','Kivou'):

        torn_key = config["torn_keys"][player_name]
        skill_data = safe_get(f"https://api.torn.com/user/?selections=skills&key={torn_key}")
        criminal_record = safe_get(f"https://api.torn.com/user/?selections=crimes&key={torn_key}")["criminalrecord"]
        crimes2_data, crimes2_header = parse_crimes(skill_data, criminal_record, current_date_num)
        sheet_name = "Crimes2" + player_name
        write_to_sheet(gc, spreadsheet_id, sheet_name, computer_name, crimes2_data, crimes2_header)

if __name__ == "__main__":
    main()