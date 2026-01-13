from jpr_lib import load_config, safe_get, python_date_to_excel_number
import gspread
from datetime import datetime, timezone
from gspread.utils import ValueInputOption

def get_stats(torn_key: str):
    battle_stats = safe_get(url="https://api.torn.com/v2/user/personalstats?cat=battle_stats",
                            torn_key=torn_key)["personalstats"]["battle_stats"]
    jobs_stats = safe_get(url="https://api.torn.com/v2/user/personalstats?cat=jobs",
                    torn_key=torn_key)["personalstats"]["jobs"]["stats"]
    return battle_stats, jobs_stats

def main():
    # --- Get configuration (api keys, data, google sheets access...) ---
    config = load_config()
    torn_keys = config["torn_keys"]
    torn_project_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    computer_name = config.get("computer", "unknown")
    date_now = datetime.now(timezone.utc)
    current_date_num = python_date_to_excel_number(date_now)

    gc = gspread.service_account(filename=torn_project_keyfile)
    spreadsheet_id = config["sheet_keys"]["torn_stats"]

    for player in ("Kivou","Kwartz"):

        # --- Get stats data ---
        bs, js = get_stats(torn_key=torn_keys[player])

        # --- Spreadsheet write ---
        ws = gc.open_by_key(spreadsheet_id).worksheet(f'Stats{player}')
        row = int(ws.cell(1,2).value) + 1

        # --- Delta and average formulas (computed in spreadsheet) ---
        daily_delta_bs = f'=IF(ROW()<=3,"",B{row}-B{row - 1})'
        ten_day_delta_bs_avg = f'=IF(ROW()<=12,"",(B{row}-B{row - 10})/10)'
        year_delta_bs_avg = f'=IF(ROW()<=367,"",(B{row}-B{row - 365})/365000000)'
        daily_delta_js = f'=IF(ROW()<=3,"",M{row}-M{row - 1})'
        two_month_delta_js_avg = f'=IF(ROW()<=62,"",(M{row}-M{row - 60})/60)'

        stats_row = [[
            current_date_num,  # A
            bs["total"],  # B total stats
            bs["dexterity"],  # C
            bs["strength"],  # D
            bs["defense"],  # E
            bs["speed"],  # F
            daily_delta_bs,  # G
            ten_day_delta_bs_avg,  # H
            year_delta_bs_avg,  # I
            js["manual"],  # J
            js["intelligence"],  # K
            js["endurance"],  #
            js["total"],  # M
            daily_delta_js, # N
            two_month_delta_js_avg # O
            ]]

        row_range = f"A{row}:O{row}"
        ws.update(range_name=row_range,
                  values=stats_row,
                  value_input_option=ValueInputOption.user_entered)
        ws.update_cell(2,1, f"updated by {computer_name}")

    ws = gc.open_by_key(spreadsheet_id).worksheet(f'StatsKwartz')
    ws.update(range_name=f"P{row}",
              values=[[f"=B{row}-StatsKivou!B{row}"]],
              value_input_option=ValueInputOption.user_entered)


if __name__ == "__main__":
    main()