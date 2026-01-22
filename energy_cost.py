from jpr_lib import load_config, safe_get, vladar_formula, point_value_averaged
from pprint import pprint
import matplotlib.pyplot as plt
from datetime import datetime, timezone

verbose = True

# -------------------------
# Configuration & Utilities
# -------------------------
def get_config():
    """Load and return Torn API keys, spreadsheet info, and computer name."""
    config = load_config()
    torn_keys = config["torn_keys"]
    data_path = config["data_path"]
    json_keyfile = data_path + config["sheet_keys"]["torn_project_json"]
    spreadsheet_id = config["sheet_keys"]["NubTV"]
    computer_name = config.get("computer", "unknown")
    return torn_keys, json_keyfile, spreadsheet_id, computer_name

def rename_dict_keys(d: dict, mapping: dict) -> dict:
    """Return a dictionary with keys renamed according to a mapping."""
    return {mapping[k]: v for k, v in d.items()}

# -------------------------
# Torn API Data Fetching
# -------------------------
def fetch_items_price(torn_key: str, cat: str, wanted: tuple) -> dict:
    """
    Fetch item market prices from Torn API.
    :param torn_key: Torn API key
    :param cat: Category name
    :param wanted: tuple with item names
    :return: dict {item_name: market_price}
    """
    items = safe_get(
        url=f"https://api.torn.com/v2/torn/items?cat={cat}",
        torn_key=torn_key
    )["items"]
    return {item["name"]: item["value"]["market_price"] for item in items if item["name"] in wanted}

def fetch_stats(torn_key: str) -> dict:
    """Fetch personal battle stats from Torn API."""
    stats = safe_get(
        url="https://api.torn.com/v2/user/personalstats?cat=battle_stats",
        torn_key=torn_key
    )["personalstats"]["battle_stats"]
    stats.pop("total", None)
    return stats

# -------------------------
# SE Cost Computation
# -------------------------
def compute_se_costs(my_stats: dict, gym_bonus: dict, se_price: float, perks_percent: list,
                     energy_per_train: int, happy: float) -> tuple[dict, dict]:
    """
    Compute stat enhancer (SE) equivalent cost for 25 energy.
    :return: (SE_cost_dict, delta_stats_dict)
    """
    delta_stats = {}
    se_costs = {}
    for stat_key, current_stat_value in my_stats.items():
        result = vladar_formula(
            stat_key=stat_key,
            current_stat=current_stat_value,
            gym_bonus=gym_bonus[stat_key],
            energy_per_train=energy_per_train,
            happy=float(happy),
            perks_percent=perks_percent,
            include_random=False
        )
        delta_stats[stat_key] = result
        se_costs[stat_key] = 100 * result / current_stat_value * se_price

    # Rename keys for display
    mapping = {"strength": "SE str", "defense": "SE def", "speed": "SE spe", "dexterity": "SE dex"}
    se_costs_renamed = rename_dict_keys(se_costs, mapping)
    return se_costs_renamed, delta_stats

# -------------------------
# Cost Computation
# -------------------------
def compute_cost_for_25_energy(all_prices: dict, energy: dict, se_costs: dict) -> dict:
    """Compute cost per 25 energy for all items including SE."""
    cost_for_25e = {item: all_prices[item] / energy[item] * 25 for item in all_prices}
    return cost_for_25e | se_costs  # merge dictionaries

# -------------------------
# Plotting
# -------------------------
def plot_energy_cost_bar_chart(profile, current_date_str, item_order, costs_normalized, gym_bonus, my_stats, rehab_per_xanax, happy, steadfast):
    """Plot bar chart comparing item costs per 25 energy."""
    plt.figure(figsize=(12,6))
    # default color
    colors = ["skyblue"] * (len(item_order) - 4)  # first bars
    colors += ["lightgreen"] * 4  # last 4 bars
    bars = plt.bar(item_order, costs_normalized, color=colors)

    plt.xticks(rotation=45, ha="right")
    plt.ylabel(r"Cost for 25 energy (m$)")
    plt.title(f"{profile['name']} - [{profile['id']}] - {current_date_str}\n"
              f"Gym cost comparison (with SE cost normalization)", fontsize=10)

    font_size = 10
    info1 = (f"Gym dots\n"
             f"def: {gym_bonus['defense']:.1f}\n"
             f"dex: {gym_bonus['dexterity']:.1f}\n"
             f"str: {gym_bonus['strength']:.1f}\n"
             f"spe: {gym_bonus['speed']:.1f}")
    plt.text(0.03, 0.96, info1, transform=plt.gca().transAxes, va='top', fontsize=font_size, fontfamily='monospace',
             bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3", alpha=0.8))

    info2 = (f"Rehab cost/xanax: {round(rehab_per_xanax)/1_000_000:.1f} m$\n"
             f"Happy: {happy}\n"
             f"Steadfast: {steadfast}")
    plt.text(0.03, 0.74, info2, transform=plt.gca().transAxes, va='top', fontsize=font_size, fontfamily='monospace',
             bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3", alpha=0.8))

    abbr = {'strength': 'str','defense': 'def','speed': 'spe','dexterity': 'dex'}
    stats_text = "Stats" + "".join(f"\n{abbr[k]}: {v/1_000_000_000:.3f} b" for k, v in my_stats.items())
    plt.text(0.12, 0.96, stats_text, transform=plt.gca().transAxes, va='top', fontsize=font_size, fontfamily='monospace',
             bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3", alpha=0.8))

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, f"{height:.2f}", ha='center', va='bottom')

    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

# -------------------------
# Main Function
# -------------------------
def main():

    # Load configuration
    config = load_config()
    runtime_data = config["runtime_data"]
    torn_keys = runtime_data["torn_keys"]
    now_date = datetime.now(timezone.utc)
    current_date_str = now_date.strftime("%d/%m/%Y")

    # Parameters
    torn_key = torn_keys["Kwartz"]
    perks_percent = [17, 2, 1, 1, 0, 0]
    gym_bonus = {'strength': 7.3, 'defense': 8.0, 'speed': 7.3, 'dexterity': 7.5}
    energy_per_train = 25
    happy = 5000
    se_price = 450_000_000
    rehab_per_xanax = 2_500_000
    steadfast = perks_percent[0]

    # Fetch profile and stats
    profile = safe_get(url=f"https://api.torn.com/v2/user/basic", torn_key=torn_key)["profile"]
    my_stats = fetch_stats(torn_key)

    # Compute SE costs
    se_equivalent_25e_cost, delta_stats = compute_se_costs(my_stats, gym_bonus, se_price, perks_percent, energy_per_train, happy)

    # Fetch item prices
    drug_prices = fetch_items_price(torn_key, "Drug", ("LSD", "Xanax"))
    drug_prices["Xan + rehab"] = drug_prices["Xanax"] + rehab_per_xanax
    e_drink_prices = fetch_items_price(torn_key, "Energy Drink",
                                      ("Can of Goose Juice", "Can of Damp Valley", "Can of Crocozade",
                                       "Can of Munster", "Can of Red Cow", "Can of Taurine Elite"))
    e_drink_prices = {k.replace("Can of ", ""): v for k, v in e_drink_prices.items()}

    booster_prices = fetch_items_price(torn_key, "Booster", ("Feathery Hotel Coupon",))
    booster_prices["FHC"] = booster_prices.pop("Feathery Hotel Coupon")
    average_point_value = point_value_averaged(torn_key=torn_key, n_average=8, verbose=False)
    booster_prices["Refill"] = 30 * average_point_value

    # Combine all prices
    all_prices = drug_prices | e_drink_prices | booster_prices
    energy = {
        'Crocozade': 22.5, 'Damp Valley': 15, 'FHC': 150, 'Goose Juice': 7.5, 'LSD': 50,
        'Munster': 30, 'Red Cow': 37.5, 'Refill': 150, 'Taurine Elite': 45, 'Xanax': 250, 'Xan + rehab': 250
    }
    cost_for_25_energy_final = compute_cost_for_25_energy(all_prices, energy, se_equivalent_25e_cost)

    # Prepare plotting order
    item_order = ['LSD', 'Refill', 'Xanax', 'Xan + rehab', 'Goose Juice', 'Damp Valley', 'Crocozade',
                  'Munster', 'Red Cow', 'Taurine Elite', 'FHC', 'SE def', 'SE str', 'SE spe', 'SE dex']
    costs_normalized = [cost_for_25_energy_final[item]/1_000_000 for item in item_order]

    # Sort SE items
    se_items = item_order[-4:]
    se_costs = [se_equivalent_25e_cost[item]/1_000_000 for item in se_items]
    se_sorted = sorted(zip(se_items, se_costs), key=lambda x: x[1], reverse=False)
    se_items_sorted, se_costs_sorted = zip(*se_sorted)
    item_order = item_order[:-4] + list(se_items_sorted)
    costs_normalized = costs_normalized[:-4] + list(se_costs_sorted)

    # print some results
    if verbose:
        print(f"Torn stats: {my_stats}")
        print(f"SE equivalent 25e price: {se_equivalent_25e_cost}")
        pprint(e_drink_prices)
    # Plot
    plot_energy_cost_bar_chart(profile, current_date_str, item_order, costs_normalized, gym_bonus, my_stats, rehab_per_xanax, happy, steadfast)


if __name__ == "__main__":
    main()
