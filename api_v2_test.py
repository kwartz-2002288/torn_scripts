import requests
from pprint import pprint

API_KEY = "wOvJMKAF3uptrV9E"

url = "https://api.torn.com/v2/torn/shoplifting"

headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Accept": "application/json",
}

response = requests.get(url, headers=headers)
response.raise_for_status()  # lève une exception si 4xx / 5xx

data = response.json()
pprint(data)
