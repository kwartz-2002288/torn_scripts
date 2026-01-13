from jpr_lib import load_config, safe_get, python_date_to_excel_number, parse_amount
import gspread
from gspread.utils import ValueInputOption
from datetime import datetime, timezone

def get_networth(torn_key : str):
    networth = safe_get(url=f'https://api.torn.com/v2/user/networth', torn_key=torn_key)['networth']
    return networth['total'],networth['stockmarket'],networth['company'],networth['vault']

def get_faction_balance(torn_key : str):
        profile = safe_get(url=f'https://api.torn.com/v2/user/basic', torn_key=torn_key)['profile']
        member_id = profile['id']
        members = safe_get(url=f'https://api.torn.com/v2/faction/balance', torn_key=torn_key)['balance']['members']
        for member in members:
            if member.get("id") == member_id:
                return member.get("money")
        return None

def get_company_funds(torn_key: str):
#
#   ATTENTION: uses torn API version 1 (not yet available in version 2)
#   returns the cash in company vault
#
    company_detailed = safe_get(
        url=f'https://api.torn.com/company/?selections=detailed&key={torn_key}')['company_detailed']
    return company_detailed['company_funds']

def evaluate_networth_correction(networth_corrections, torn_key):
    stocks_lent = networth_corrections['stocks_lent']
    stocks = safe_get(url='https://api.torn.com/v2/torn/stocks', torn_key=torn_key)['stocks']
    stocks_lent_value = 0
    for lent in stocks_lent:
        stock = stocks[lent["stock_id"]]
        stocks_lent_value += (2**lent["increments"] - 1)*stock["current_price"]*stock["benefit"]["requirement"]
    nub_rig_investment = parse_amount(networth_corrections['nub_rig_investment'])
    nub_tv_delta = parse_amount(networth_corrections['nub_tv_delta'])
    company_correction = nub_rig_investment + nub_tv_delta
    return company_correction, stocks_lent_value

def main():
    # --- Get configuration (api keys, data, google sheets access...) ---
    config = load_config()
    torn_keys = config["torn_keys"]
    torn_project_keyfile = config["data_path"] + config["sheet_keys"]["torn_project_json"]
    computer_name = config["computer"]
    networth_corrections = config["various_torn_data"]["networth_corrections"]

    gc = gspread.service_account(filename=torn_project_keyfile)
    spreadsheet_id = config["sheet_keys"]["torn_stats"]
    ws = gc.open_by_key(spreadsheet_id).worksheet('NW')

    # --- Get networth information ---
    faction_balance_total = (get_faction_balance(torn_keys['Kivou']) +
                             get_faction_balance(torn_keys['Kwartz']))
    networth_kivou, stock_kivou, company_kivou, vault_kivou = get_networth(torn_keys['Kivou'])
    networth_kwartz, stock_kwartz, company_kwartz, vault_kwartz = get_networth(torn_keys['Kwartz'])

    # --- Aggregates ---
    networth_total = networth_kivou + networth_kwartz
    stock_total = stock_kivou + stock_kwartz
    company_total = company_kivou + company_kwartz
    company_funds = get_company_funds(torn_keys['Kwartz'])
    pi_vault_total = vault_kivou + vault_kwartz
    cash_total = pi_vault_total + faction_balance_total + company_funds

    company_correction, stocks_lent_value = evaluate_networth_correction(
        networth_corrections, torn_keys['Kwartz'])

    networth_corrected = networth_total + faction_balance_total + company_correction + stocks_lent_value
    stock_total_corrected = stock_total + stocks_lent_value

    date_now = datetime.now(timezone.utc)
    current_date_num = python_date_to_excel_number(date_now)

    # --- Spreadsheet write ---
    row = int(ws.cell(1,2).value) + 1
    stats_row = [[
        current_date_num,  # A
        networth_total,  # B
        stock_total,  # C
        company_total,  # D
        faction_balance_total,  # E
        pi_vault_total,  # F
        stock_total_corrected,  # G
        networth_corrected,  # H
        networth_kwartz / 1_000_000_000,  # I
        networth_kivou / 1_000_000_000,  # J
        cash_total,  # K
        f'=IF(ROW()<=5,"",H{row}-H{row - 1})',  # L  daily delta
        f'=IF(ROW()<=34,"",H{row}-H{row - 30})'  # M  30-day delta
    ]]
    row_range = f"A{row}:M{row}"
    ws.update(range_name=row_range, values=stats_row, value_input_option=ValueInputOption.user_entered)
    ws.update_cell(2, 2, computer_name)


if __name__ == "__main__":
    main()