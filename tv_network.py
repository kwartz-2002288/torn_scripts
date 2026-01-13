from jpr_lib import load_config, safe_get, python_date_to_excel_number, parse_amount
import gspread
from gspread.utils import ValueInputOption
from datetime import datetime, timezone
#from pprint import pprint

def get_config():
    """
    Load and extract configuration values needed for the script.
    """
    config = load_config()
    torn_keys = config["torn_keys"]
    data_path = config["data_path"]
    torn_project_keys = data_path + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["NubTV"]
    computer_name = config["computer"]
    tv_networks_data = config["various_torn_data"]["tv_networks_data"]
    tv_data = {key: parse_amount(value) for key, value in tv_networks_data.items()}
    return torn_keys, torn_project_keys, spreadsheet_id, computer_name, tv_data


def fetch_company_data(torn_key: str):
    """
    Call Torn API to fetch company employees, detailed info, and profile.
    """
    base_url = f"https://api.torn.com/company/?key={torn_key}&selections="
    company_employees = safe_get(base_url + "employees")["company_employees"]
    company_detailed = safe_get(base_url + "detailed")["company_detailed"]
    company_profile = safe_get(base_url + "profile")["company"]
    return company_employees, company_detailed, company_profile


def parse_employees(company_employees: dict, now_date: datetime, director_wage: int):
    """
    Parse and aggregate employee data for spreadsheet output and totals.
    """
    employees = []
    wages_total = director_wage  # director wage not included in API
    working_stats_eff_total = 0
    settle_total = 0
    EE_total = 0
    director_education_total = 0
    addiction_total = 0
    inactivity_total = 0
    company_effectiveness_total = 0

    for employee_id, employee in company_employees.items():
        wage = employee["wage"]
        wages_total += wage

        working_stats = employee["effectiveness"].get("working_stats", 0)
        working_stats_eff_total += working_stats

        merits = employee["effectiveness"].get("merits", 0)
        EE_total += merits

        addiction = employee["effectiveness"].get("addiction", 0)
        addiction_total += addiction

        settled_in = employee["effectiveness"].get("settled_in", 0)
        settle_total += settled_in

        director_education = employee["effectiveness"].get("director_education", 0)
        director_education_total += director_education

        effectiveness_total = employee["effectiveness"].get("total", 0)
        company_effectiveness_total += effectiveness_total

        inactivity = employee["effectiveness"].get("inactivity", 0)
        inactivity_total += inactivity

        # Calculate AFK time in days and hours
        timestamp = employee["last_action"]["timestamp"]
        employee_date = datetime.fromtimestamp(timestamp, timezone.utc)
        afk_duration = now_date - employee_date
        afk_days = afk_duration.days
        afk_hours, _ = divmod(afk_duration.seconds, 3600)

        # Calculate combo of highest two stats
        stats = [employee[k] for k in ["intelligence", "endurance", "manual_labor"]]
        stats.sort(reverse=True)
        stats_combo = stats[0] + stats[1]

        INT, END, MAN = employee["intelligence"], employee["endurance"], employee["manual_labor"]

        employees.append([
            employee_id,
            employee["name"],
            employee["position"],
            employee["days_in_company"],
            merits,
            working_stats,
            INT, END, MAN,
            stats_combo,
            wage,
            addiction,
            settled_in,
            director_education,
            effectiveness_total,
            afk_days,
            afk_hours,
            inactivity
        ])

    header = [
        "id", "name", "position",
        "days_in", "merits", "ws",
        "INT", "END", "MAN",
        "stats_combo", "wage", "addiction",
        "settled_in", "dir_educ", "eff_tot",
        "afk_d", "afk_h", "inactivity"
    ]

    # Sort employees by 'position' ascending
    sort_index = header.index("position")
    employees.sort(key=lambda x: x[sort_index])

    return [header] + employees, wages_total, working_stats_eff_total, settle_total, EE_total, director_education_total, addiction_total, inactivity_total, company_effectiveness_total


def update_employees_sheet(gc, spreadsheet_id: str, employees: list):
    """
    Clear and update 'employees_raw' worksheet with employee data.
    """
    ws = gc.open_by_key(spreadsheet_id).worksheet('employees_raw')
    ws.clear()
    ws.update(range_name="A1:Z51", values=employees)


def update_wages_sheet(gc, spreadsheet_id: str, computer_name: str, current_date_str: str):
    """
    Update 'wages' worksheet with update timestamp and computer name.
    """
    ws = gc.open_by_key(spreadsheet_id).worksheet('wages')
    ws.update_cell(1, 1, f"Updated by {computer_name} {current_date_str} TCT")


def update_evolution_sheet(
        gc, spreadsheet_id: str, company_profile: dict, company_detailed: dict,
        current_date_num: float, wages_total: int,
        working_stats_eff_total: int, settle_total: int, EE_total: int,
        director_education_total: int, addiction_total: int, inactivity_total: int,
        company_effectiveness_total: int, tv_data: dict
):
    """Parse tv_data and update evolution sheet."""

    total_investment = tv_data["company_price"] + tv_data["sys_stock_price"] + tv_data["vault_contribution"]
    KK_investment = tv_data["KK_share"]+ tv_data["sys_stock_price"]+ tv_data["vault_contribution"]

    daily_income = company_profile["daily_income"]
    advertising_budget = company_detailed["advertising_budget"]

    daily_profit = daily_income - wages_total - advertising_budget
    minimum_funds = 7 * (wages_total - tv_data["director_wage"] + advertising_budget)
    ROI = daily_profit * 365 / total_investment
    ROI2 = ROI + (tv_data["director_wage"] + tv_data["kivou_wage"]) * 365 / KK_investment

    company_effectiveness_max = (company_effectiveness_total - inactivity_total - addiction_total)
    efficiency_loss = (-inactivity_total - addiction_total) / company_effectiveness_max


    ws_evo = gc.open_by_key(spreadsheet_id).worksheet('evolution')
    row = int(ws_evo.cell(1, 3).value) + 1   #  row where to write data
    evolution_row = [
        current_date_num,
        company_profile["name"],
        company_profile["rating"],
        company_detailed["popularity"],
        company_detailed["trains_available"],
        company_detailed["efficiency"],
        company_detailed["environment"],
        working_stats_eff_total,
        settle_total,
        EE_total,
        director_education_total,
        addiction_total,
        inactivity_total,
        company_effectiveness_total,
        company_effectiveness_max,
        efficiency_loss,
        company_profile["weekly_customers"],
        company_profile["daily_customers"],
        company_detailed["value"] / 1_000_000_000,
        company_detailed["company_funds"] / 1_000_000,
        minimum_funds / 1_000_000,
        company_profile["weekly_income"] / 1_000_000,
        company_profile["daily_income"] / 1_000_000,
        wages_total / 1_000_000,
        advertising_budget / 1_000_000,
        daily_profit / 1_000_000,
        ROI,
        ROI2,
        f'=IF(ROW()<=33,"",SUM(Z{row - 29}:Z{row}))'  # AC
    ]
    row_range = f"A{row}:AC{row}"
    ws_evo.update(range_name=row_range, values=[evolution_row], value_input_option=ValueInputOption.user_entered)

def main():

    torn_keys, torn_project_keys, spreadsheet_id, computer_name, tv_data = get_config()
    torn_key = torn_keys["Kwartz"]
    gc = gspread.service_account(torn_project_keys)

    company_employees, company_detailed, company_profile = (
        fetch_company_data(torn_key))

    now_date = datetime.now(timezone.utc)
    current_date_str = now_date.strftime("%d/%m/%Y %H:%M:%S")
    current_date_num = python_date_to_excel_number(now_date)

    (employees, wages_total, working_stats_eff_total, settle_total, EE_total, director_education_total,
     addiction_total, inactivity_total, company_effectiveness_total) = parse_employees(
        company_employees, now_date, tv_data["director_wage"])

    update_employees_sheet(gc, spreadsheet_id, employees)
    update_wages_sheet(gc, spreadsheet_id, computer_name, current_date_str)
    update_evolution_sheet(gc, spreadsheet_id, company_profile, company_detailed,
                           current_date_num, wages_total,
                           working_stats_eff_total, settle_total, EE_total,
                           director_education_total, addiction_total, inactivity_total,
                           company_effectiveness_total, tv_data)

if __name__ == "__main__":
    main()
