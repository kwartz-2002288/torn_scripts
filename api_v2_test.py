import requests
from pprint import pprint

API_KEY = "wOvJMKAF3uptrV9E"

url = "https://api.torn.com/company/?selections=employees&key=wOvJMKAF3uptrV9E"



url = "https://api.torn.com/v2/company/?selections=detailed"
url = "https://api.torn.com/v2/company/?selections=employees"
url = "https://api.torn.com/v2/company/?selections=profile"
headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Accept": "application/json",
}



response = requests.get(url, headers=headers)
#response = requests.get(url)
response.raise_for_status()  # lève une exception si 4xx / 5xx

data = response.json()
pprint(data)
