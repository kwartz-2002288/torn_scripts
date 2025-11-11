import requests, json
from datetime import datetime, timezone

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
    Returns a message indicating success or the type of error.
    """
    free_user = api_keys["free_user"]
    free_api_key = api_keys["free_apikey"]
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={free_user}&pass={free_api_key}&msg={message}"
    response = requests.get(url)
    return FREE_ERRORS.get(response.status_code, "Unknown error")


def safe_get(url: str, verbose: bool = False) -> dict:
    """
    Secure GET request that checks for HTTP and Torn API errors.

    Parameters:
        url (str): The full URL to call.
        verbose (bool): If True, print Torn API errors.

    Returns:
        dict: Parsed JSON response from the API.

    Raises:
        Exception: If HTTP status is not 200 or Torn API returns an error.
    """
    r = requests.get(url)

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

def get_yata_targets(path):
    """"
    get the targets exported by YATA in path/target_list.json and load in a dictionary
    """
    with open(path+'target_list.json','r') as f:
        return json.load(f)