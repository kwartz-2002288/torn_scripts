from jpr_lib import load_config, safe_get, datetime_to_excel_date
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
    # Load configuration
    config = load_config()
    runtime_data = config["runtime_data"]
    service_file = config["data_path"] + runtime_data["google"]["service_account_file"]
    computer = config["computer"]

    torn_keys = runtime_data["torn_keys"]
    spreadsheet_id = runtime_data["spreadsheet_ids"]["torn_stats"]

    # Connect to Google Sheets
    gs_client = gspread.service_account(filename=service_file) #

    current_date_excel = datetime_to_excel_date(datetime.now(timezone.utc))

    for player in ("Kivou","Kwartz"):

        # --- Get stats data ---
        bs, js = get_stats(torn_key=torn_keys[player])

        # --- Spreadsheet write ---
        ws = gs_client.open_by_key(spreadsheet_id).worksheet(f'Stats{player}')
        row = int(ws.cell(1,2).value) + 1

        # --- Delta and average formulas (computed in spreadsheet) ---
        daily_delta_bs = f'=IF(ROW()<=3,"",B{row}-B{row - 1})'
        ten_day_delta_bs_avg = f'=IF(ROW()<=12,"",(B{row}-B{row - 10})/10)'
        year_delta_bs_avg = f'=IF(ROW()<=367,"",(B{row}-B{row - 365})/365000000)'
        daily_delta_js = f'=IF(ROW()<=3,"",M{row}-M{row - 1})'
        two_month_delta_js_avg = f'=IF(ROW()<=62,"",(M{row}-M{row - 60})/60)'

        stats_row = [[
            current_date_excel,  # A
            bs["total"],  # B total combat stats
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
            js["total"],  # M total work stats
            daily_delta_js, # N
            two_month_delta_js_avg # O
            ]]

        row_range = f"A{row}:O{row}"
        ws.update(range_name=row_range,
                  values=stats_row,
                  value_input_option=ValueInputOption.user_entered)
        ws.update_cell(2,1, f"updated by {computer}")

    ws = gs_client.open_by_key(spreadsheet_id).worksheet(f'StatsKwartz')
    ws.update(range_name=f"P{row}",
              values=[[f"=B{row}-StatsKivou!B{row}"]],
              value_input_option=ValueInputOption.user_entered)


if __name__ == "__main__":
    main()