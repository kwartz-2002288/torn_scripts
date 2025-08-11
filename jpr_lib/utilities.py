import requests

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