from jpr_lib import load_config, safe_get
from datetime import datetime
from itertools import product
import gspread


CACHE_IDS = {
    1118: "AC",
    1121: "MAC",
    1119: "MC",
    1120: "SAC",
    1122: "HAC",
}

def find_best_transfers(winner_caches, loser_caches, cache_prices,
                        winner_target_pct):

    initial_winner_value = sum(
        winner_caches[item_id] * cache_prices[item_id]
        for item_id in CACHE_IDS
    )

    initial_loser_value = sum(
        loser_caches[item_id] * cache_prices[item_id]
        for item_id in CACHE_IDS
    )

    total_value = initial_winner_value + initial_loser_value
    loser_target_value = total_value * (1 - winner_target_pct)
    target_transfer = loser_target_value - initial_loser_value

    solutions = []

    ranges = [
        range(winner_caches[item_id] + 1)
        for item_id in CACHE_IDS
    ]

    for quantities in product(*ranges):
        cache_transfer_value = sum(
            quantity * cache_prices[item_id]
            for item_id, quantity in zip(CACHE_IDS, quantities)
        )

        money = target_transfer - cache_transfer_value

        solutions.append({
            "quantities": quantities,
            "cache_value": cache_transfer_value,
            "money": money,
        })

    solutions.sort(key=lambda solution: abs(solution["money"]))

    return solutions[:3]

def get_ranked_war_report(torn_key: str, war_id: int):
    data = safe_get(
        url=f"https://api.torn.com/v2/faction/{war_id}/rankedwarreport",
        torn_key=torn_key
    )

    report = data["rankedwarreport"]
    winner_id = report["winner"]

    winner = next(
        faction for faction in report["factions"]
        if faction["id"] == winner_id
    )

    loser = next(
        faction for faction in report["factions"]
        if faction["id"] != winner_id
    )

    def get_caches(faction):
        caches = {cache_id: 0 for cache_id in CACHE_IDS}

        for item in faction["rewards"]["items"]:
            if item["id"] in CACHE_IDS:
                caches[item["id"]] = item["quantity"]

        return caches

    return {
        "winner": {
            "id": winner["id"],
            "name": winner["name"],
            "caches": get_caches(winner),
        },
        "loser": {
            "id": loser["id"],
            "name": loser["name"],
            "caches": get_caches(loser),
        },
    }

def get_last_finished_ranked_war(torn_key: str):
    data = safe_get(
        url="https://api.torn.com/v2/faction/rankedwars?offset=0&limit=2&sort=DESC",
        torn_key=torn_key
    )

    for war in data["rankedwars"]:
        if war["end"] != 0 and war["winner"] is not None:
            return war

    raise RuntimeError("No finished ranked war found")

def get_cache_prices(torn_key: str):
    data = safe_get(
        url="https://api.torn.com/v2/torn/items?cat=Supply%20Pack&sort=ASC",
        torn_key=torn_key
    )

    return {
        item["id"]: item["value"]["market_price"]
        for item in data["items"]
        if item["id"] in CACHE_IDS
    }


def main():
    # Load configuration
    config = load_config()
    computer = config["computer"]
    runtime_data = config["runtime_data"]

    torn_key = runtime_data["torn_keys"]["Kwartz"]
    service_file = (
        config["data_path"]
        + runtime_data["google"]["service_account_file"]
    )
    spreadsheet_id = runtime_data["spreadsheet_ids"]["termed_rw"]

    # Get cache market prices from Torn
    cache_prices = get_cache_prices(torn_key)

    # Connect to Google Sheets
    gs_client = gspread.service_account(filename=service_file)
    ws = gs_client.open_by_key(spreadsheet_id).worksheet("Repartition")

    values = [
        [cache_prices[item_id] / 1_000_000]
        for item_id in CACHE_IDS
    ]

    # Update B4:B8 in one request
    ws.update(
        range_name="B4:B8",
        values=values
    )
    update_time = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
    ws.update_acell("B14", update_time)
    ws.update_acell("B13", "updated by\n" + computer)

    print("Cache prices updated:")
    for abbreviation, value in zip(CACHE_IDS.values(), values):
        print(f"{abbreviation}: {value[0]:.3f} m$")

    war = get_last_finished_ranked_war(torn_key)

    print(
        f'Last finished war: {war["id"]} '
        f'- winner ID: {war["winner"]}'
    )

    report = get_ranked_war_report(torn_key, war["id"])
    winner_values = [
        [report["winner"]["caches"][item_id]]
        for item_id in CACHE_IDS
    ]

    loser_values = [
        [report["loser"]["caches"][item_id]]
        for item_id in CACHE_IDS
    ]

    ws.update(
        range_name="E4:E8",
        values=winner_values
    )

    ws.update(
        range_name="G4:G8",
        values=loser_values
    )
    print(f'Winner: {report["winner"]["name"]}')
    for item_id, quantity in report["winner"]["caches"].items():
        print(f'  {CACHE_IDS[item_id]}: {quantity}')

    print(f'Loser: {report["loser"]["name"]}')
    for item_id, quantity in report["loser"]["caches"].items():
        print(f'  {CACHE_IDS[item_id]}: {quantity}')
    # Read target Winner percentage from spreadsheet
    winner_target_pct = float(ws.acell("K4").value.strip("%")) / 100

    # Find good cache transfers
    best, second_best, third_best = find_best_transfers(
        report["winner"]["caches"],
        report["loser"]["caches"],
        cache_prices,
        winner_target_pct
    )

    # Write the 3 proposed solutions
    for column, solution in zip(
            ("L", "M", "N"),
            (best, second_best, third_best)
    ):
        ws.update(
            range_name=f"{column}14:{column}18",
            values=[[quantity] for quantity in solution["quantities"]]
        )

        ws.update_acell(
            f"{column}20",
            solution["money"] / 1_000_000
        )

    for rank, solution in enumerate(
        (best, second_best, third_best),
        start=1
    ):
        print(f"\nSolution {rank}:")

        for item_id, quantity in zip(CACHE_IDS, solution["quantities"]):
            print(f"  {CACHE_IDS[item_id]}: {quantity}")

        print(f'  Cache value: {solution["cache_value"] / 1_000_000:.3f} m$')
        print(f'  Money compensation: {solution["money"] / 1_000_000:.3f} m$')

if __name__ == "__main__":
    main()