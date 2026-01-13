import requests, json
import math, random
from datetime import datetime, timezone
from pprint import pprint

#
# Various utilities for torn
#

# send_sms (Use Free Mobile API)
# safe_get (Secure GET request that checks for HTTP and Torn API errors)
# python_date_to_excel_number (Convert a python date to Google/Excel date)
# get_yata_targets
#

FREE_ERRORS = {
    200: "SMS sent successfully.",
    400: "Missing parameter. One or more required parameters were not provided.",
    402: "Too many SMS sent in a short period. SMS sending is temporarily blocked.",
    403: "Incorrect credentials. The provided user ID/API key pair is invalid.",
    500: "Server error. A problem occurred on Free Mobile's server."
}

def send_sms(message: str, api_keys: dict) -> str:
    """
    Send SMS message to free_user phone using Free Mobile API credentials.
    Returns a message indicating success or the error type.
    """
    free_user = api_keys["free_user"]
    free_api_key = api_keys["free_apikey"]
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={free_user}&pass={free_api_key}&msg={message}"
    response = requests.get(url)
    return FREE_ERRORS.get(response.status_code, "Unknown error")

def safe_get(url: str, verbose: bool = False, torn_key: str = None) -> dict:
    """
    Secure GET request that checks for HTTP and Torn API errors.
    Supports both V1 (key in URL) and V2 (key in Authorization header) authentication.
    Parameters:
        url (str): The full URL to call.
                   For V1: Must include the key in the URL (e.g. "?key=..." or "&key=...").
                   For V2: Must NOT include the key in the URL.
        verbose (bool): If True, print Torn API errors.
        torn_key (str): Torn API key for V2 authentication.
                           If None, assumes V1 authentication (key in URL).
    Returns:
        dict: Parsed JSON response from the API.
    Raises:
        Exception: If HTTP status is not 200 or Torn API returns an error.
    """
    headers = None
    if torn_key is not None:
        # V2: Use Authorization header
        headers = {
            "accept": "application/json",
            "Authorization": f"ApiKey {torn_key}"
        }
        # Ensure the key is NOT in the URL for V2
        if "key=" in url:
            raise ValueError("For V2, the key must NOT be in the URL. Use torn_key parameter instead.")

    # Make the request
    r = requests.get(url, headers=headers)

    # Check HTTP status
    if r.status_code != 200:
        raise Exception(f"HTTP error ({r.status_code}): {url}")

    data = r.json()

    # Check for Torn API error in JSON
    if "error" in data:
        code = data["error"]["code"]
        msg = data["error"]["error"]
        full_msg = f"Torn API error {code}: {msg}"
        if verbose:
            print(full_msg)
        raise Exception(full_msg)

    return data

def python_date_to_excel_number(date):
    """
    Convert a python date (utc datetime format)
    to a number representing a date in a Google sheet
    """
    # Define the reference date for Google Sheets (December 30, 1899)
    reference_date = datetime(1899, 12, 30, tzinfo=timezone.utc)
    # Calculate the difference in days
    days_difference = (date - reference_date).days
    # Calculate the fraction of the day
    fraction_of_day = (date - datetime(date.year, date.month, date.day,
        tzinfo=timezone.utc)).total_seconds() / 86400.0  # 86400 seconds in a day
    # Calculate the total number
    date_number = days_difference + fraction_of_day
    return date_number


def timestamp_to_date(ts: int) -> str:
    """
    Convert a Unix timestamp (seconds) to a human-readable date string.
    Args:
        ts (int): Unix timestamp in seconds.
    Returns:
        str: Date in 'YYYY-MM-DD HH:MM:SS' format.
    """
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

# --------------------------------------------------------------------
# Vladar formula : Stat constants (A, B, C) for each stat in Torn
# --------------------------------------------------------------------
STAT_CONSTANTS = {
    "strength":  {"base_factor_A": 1600.0, "base_factor_B": 1700.0, "random_range_C": 700},
    "speed":     {"base_factor_A": 1600.0, "base_factor_B": 2000.0, "random_range_C": 1350},
    "dexterity": {"base_factor_A": 1800.0, "base_factor_B": 1500.0, "random_range_C": 1000},
    "defense":   {"base_factor_A": 2100.0, "base_factor_B": -600.0, "random_range_C": 1500},
}
# --------------------------------------------------------------------
# Compute Torn stat gain for one train (delta_stat)
# --------------------------------------------------------------------

def vladar_formula(
    stat_key: str,
    current_stat: float,
    gym_bonus: float,
    energy_per_train: float,
    happy: float,
    perks_percent: list[int],  #
    include_random: bool = False,
    random_seed: int | None = None,
) -> float:
    """
    Calculate the estimated stat gain for one training session in Torn.

    Parameters
    ----------
    stat_key : str
        Name of the stat to train ('strength', 'speed', 'dexterity', 'defense').
    current_stat : float
        Current total of the stat being trained.
    gym_bonus : float
        Gym dots divided by 10 (e.g., 73 dots → 7.3).
    energy_per_train : float
        Energy spent per training session (5, 10, 25, 50).
    happy : float
        Starting happiness.
    perks_percent : list[int]
        Gym perks % as:
        - faction perk
        - property perk
        - education stat-specific perk
        - education general perk
        - job perk
        - book perk
        Example:
            perks_percent = [15, 2, 1, 1, 0, 0]

    include_random : bool, optional
        Whether to include the ±C random term (default False).
    random_seed : int or None, optional
        Seed for random number generation to get reproducible results (default None).

    Returns
    -------
        delta_stat : float
            Estimated stat gain

    """
    key = stat_key.lower()
    if key not in STAT_CONSTANTS:
        raise ValueError(f"Invalid stat '{stat_key}'. Choose from {list(STAT_CONSTANTS.keys())}.")

    const = STAT_CONSTANTS[key]
    A = const["base_factor_A"]
    B = const["base_factor_B"]
    C = const["random_range_C"]

    # --- Soft cap for current_stat > 50M ---
    if current_stat < 50_000_000:
        effective_stat = current_stat
    else:
        effective_stat = 50_000_000 + (current_stat - 50_000_000) / (8.77635 * math.log10(current_stat))

    # Multiplier with double rounding
    ln_value = math.log(1 + happy / 250.0)
    ln_rounded = round(ln_value, 4)
    multiplier = round(1.0 + 0.07 * ln_rounded, 4)

    # Additive terms
    term_from_stat = effective_stat * multiplier
    term_from_happy = 8.0 * (happy ** 1.05)
    term_from_A = (1.0 - (happy / 99999.0) ** 2.0) * A
    term_from_B = B

    # Random term optional
    rand_term = 0
    if include_random:
        if random_seed is not None:
            random.seed(random_seed)
        rand_term = random.randint(-C, C)
    # Base sum
    base_sum = term_from_stat + term_from_happy + term_from_A + term_from_B + rand_term
    # Multiply by gym bonus and energy per train. Normalize.
    base_sum *= (1.0 / 200000.0) * gym_bonus * energy_per_train

    # Apply perks multiplicatively
    perk_multiplier = 1.0
    for p in perks_percent:
        perk_multiplier *= (1.0 + p/100.0)

    delta_stat = base_sum * perk_multiplier

    return delta_stat



def get_yata_targets(path):
    """"
    get the targets exported by YATA in path/target_list.json and load in a dictionary
    """
    with open(path+'target_list.json','r') as f:
        return json.load(f)


def col_name(col_idx: int) -> str:
    """
    Convert a 1-based column index into its spreadsheet-style column name.

    Parameters
    ----------
    col_idx : int
        Column index starting at 1 (e.g. 1 -> 'A', 26 -> 'Z', 27 -> 'AA').

    Returns
    -------
    str
        Spreadsheet column name corresponding to the given index.

    Raises
    ------
    ValueError
        If col_idx is less than 1.
    """

    ### Input validation
    if col_idx < 1:
        raise ValueError("Column index must be a positive integer starting from 1")

    ### Conversion logic
    name = ""
    while col_idx > 0:
        mod = (col_idx - 1) % 26
        name = chr(65 + mod) + name
        col_idx = (col_idx - mod) // 26

    ### Result
    return name

def point_value_averaged(torn_key: str = None, N_average: int =10, verbose: bool= False):
    """
    Compute point value on torn market point
    :param torn_key: torn API key
    :param N_average: price is computed by averaging the 10 lowest prices entries
    :param verbose: print
    :return: point value in $
    """
    data = safe_get(url=f"https://api.torn.com/v2/market/pointsmarket", torn_key=torn_key)
    points_market = data["pointsmarket"]
#
    costs = [entry["cost"] for entry in points_market.values()]
    min_cost = min(costs)
    if verbose:
#        pprint(points_market)
        print("Minimum cost:", min_cost)

    # Convert dict to list of tuples (id, info) and sort by "cost"
    sorted_entries = sorted(
        points_market.items(),
        key=lambda item: item[1]["cost"]
    )

    # Take first N entries with the lowest cost
    top = sorted_entries[:N_average]

    # Display them
    if verbose:
        print(f"cost  | quantity")
    total_cost, total_quantity = 0, 0
    for id_unused, info in top:
        cost = info["cost"]
        qty = info["quantity"]
        total_cost += qty * cost
        total_quantity += qty
        if verbose:
            print(f"{cost} | {qty}")
    average_cost = total_cost / total_quantity
    if verbose:
        print(f"average point cost: {int(average_cost)} $")
        print(f"total quantity: {total_quantity} points")
        print(f"total cost: {int(total_cost/1_000_000)} m$")
    return average_cost

def parse_amount(value: str) -> int:
    """
    Convert a string containing an underscored numeric literal into an integer.

    Example:
        "1_000_000" -> 1000000
    """
    return int(value.replace("_", "").strip())