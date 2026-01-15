from jpr_lib import load_config, safe_get, python_date_to_excel_number
import gspread
from datetime import datetime, timezone
from gspread.utils import ValueInputOption

def get_drugs_taken(torn_key: str):
    drugs_taken = safe_get(url="https://api.torn.com/v2/user/personalstats?cat=drugs",
                            torn_key=torn_key)["personalstats"]["drugs"]
    return drugs_taken

def get_drugs_price(torn_key: str) -> dict:
    drugs_list = safe_get(url="https://api.torn.com/v2/torn/items?cat=Drug",
                            torn_key=torn_key)["items"]
    drugs_price = {
        drug["name"].lower(): drug["value"]["market_price"]
        for drug in drugs_list
    }
    return drugs_price

def get_addiction_penalty(torn_key: str) -> int:
    """
    Returns the addiction percentage for a given stat (e.g. strength).
    If no addiction modifier exists, returns 0.
    """
    modifiers = safe_get(url="https://api.torn.com/v2/user/battlestats",
                            torn_key=torn_key)["battlestats"]["strength"]["modifiers"]

    for m in modifiers:
        if m["type"] == "Addiction":
            return m["value"]
    return 0


def create_row(row, keys, drugs_new, current_date_num, price, xan_od):
    n = 14
    delta_xan_avg = f'=IF(ROW()<={n}+5,"",(B{row}-B{row - n})/(A{row}-A{row - n}))'
    n = 200
    rehab_cost_avg = f'=IF(ROW()<={n}+5,"",sum(J{row}:J{row - n})/(B{row}-B{row - n}))'
    n = 198
    rehab_cost_smoothed = f'=IF(ROW()<={n}+5,"",SUMPRODUCT($N$4:$N$202,J{row - n}:J{row}))'

    drugs_list = [drugs_new[key] for key in keys]
    drugs_row = [[
        current_date_num, # col A
        *drugs_list, # col B, C, D
        price, # col E
        delta_xan_avg, # col F
        rehab_cost_avg, # col G
        rehab_cost_smoothed, # col H
        xan_od, # col I
    ]]
    return drugs_row

def main():
    # --- Get configuration (api keys, data, google sheets access...) ---
    config = load_config()
    torn_keys = config["torn_keys"]
    torn_project_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    gc = gspread.service_account(filename=torn_project_keyfile)
    spreadsheet_id = config["sheet_keys"]["torn_stats"]
    computer_name = config.get("computer", "unknown")
    date_now = datetime.now(timezone.utc)
    current_date_num = python_date_to_excel_number(date_now)

    # --- Get drugs price ---
    drugs_price = get_drugs_price(torn_keys["Kwartz"])

    for player in ("Kwartz", "Kivou"):

        # --- Get new numbers for drugs taken ---
        drugs_new = get_drugs_taken(torn_key=torn_keys[player])

        # --- Spreadsheet to update ---
        ws = gc.open_by_key(spreadsheet_id).worksheet(f'Drugs{player}')

        # --- Read old numbers for drugs taken in current row ---
        row = int(ws.cell(2,2).value)
        cells = ws.range(row, 2, row, 4)  # columns B to D
        drugs_old = [int(cell.value) for cell in cells]

        # --- Compare old and new numbers for 3 drugs ---
        keys = ["xanax", "cannabis", "vicodin"]
        drugs_changed = [k for k, v in zip(keys, drugs_old) if v != drugs_new[k]]
        if drugs_changed:
            price = drugs_price[drugs_changed[0]]
        else:
            price = 0

        # --- Detect xanax overdose ---
        total_od_old = int(ws.cell(1,6).value)
        total_od_new = drugs_new["overdoses"]
        overdosed = total_od_new > total_od_old
        xan_od = 1 if overdosed and "xanax" in drugs_changed else 0
        if overdosed:
            ws.update_cell(1,6, total_od_new)

        # --- Detect rehab sessions and update sheet ---
        rehab_old = int(ws.cell(1,10).value)
        rehab_new = drugs_new["rehabilitations"]["amount"]
        rehab_cost_total_old = int(ws.cell(2,10).value)
        rehab_cost_total_new = drugs_new["rehabilitations"]["fees"]/1_000_000
        rehab_done = rehab_new - rehab_old

        if rehab_done:
            xan_since_last_rehab_old = int(ws.cell(2, 4).value)
            ws.update_cell(row, 12, xan_since_last_rehab_old)
            ws.update_cell(1,10, rehab_new)
            ws.update_cell(2,10, rehab_cost_total_new)
            rehab_cost = rehab_cost_total_new - rehab_cost_total_old
            ws.update_cell(row, 10, rehab_cost)
            ws.update_cell(row, 11, rehab_done)

        # --- Get addiction penalty ---
        addiction = get_addiction_penalty(torn_keys[player])
        # Update the sheet only if something has changed

        row += 1
        drugs_row = create_row(row, keys, drugs_new, current_date_num, price, xan_od)

        if drugs_changed:
            row_range = f"A{row}:O{row}"
            ws.update(range_name=row_range,
                      values=drugs_row,
                      value_input_option=ValueInputOption.user_entered)
            ws.update_cell(row, 13, -addiction)
        else:
            pass

        ws.update_cell(1, 1, f"updated by {computer_name}")
        ws.update_cell(2, 1, current_date_num)

if __name__ == "__main__":
    main()