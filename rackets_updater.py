from datetime import datetime, timezone

import gspread

from jpr_lib import (
    datetime_to_excel_date, timestamp_to_excel_date,
    load_config,
    safe_get,
    send_sms,
)

def get_tracked_rackets(torn_key: str, faction_ids: set[int]) -> dict[str, dict]:
    """
    Return active rackets for allied factions, indexed by territory code.
    """
    rackets = safe_get(
        url="https://api.torn.com/v2/faction/rackets",
        torn_key=torn_key
    )["rackets"]
    return {
        r["territory"]: r
        for r in rackets
        if r["faction_id"] in faction_ids
    }

def detect_disappeared_rackets(
    spreadsheet,
    sms_account: dict,
    computer: str,
    active_territories: set[str],
) -> None:

    for ws in spreadsheet.worksheets():
        title = ws.title
        if len(title) == 3 and title.isupper() and title.isalpha() and title not in active_territories:
            records = ws.get_all_records()
            last_snapshot = records[-1] if records else None
            if not last_snapshot:
                continue
            notify_and_log_event(
                spreadsheet,
                sms_account,
                computer,
                event="disappeared",
                territory=ws.title,
                racket_name=last_snapshot["racket_name"],
                faction_name=last_snapshot["faction_name"],
                level=last_snapshot["level"],
            )
            # rename the sheet to indicate it's gone
            new_title = title.lower()
            ws.update_title(new_title)


def get_or_create_racket_sheet(spreadsheet, territory: str):
    try:
        return spreadsheet.worksheet(territory), False
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=territory, rows=100, cols=20)
        ws.append_row([
            "creation_date",
            "last_change_date",
            "faction_name",
            "faction_id",
            "racket_name",
            "level",
            "description",
            "reward_type",
            "reward_id",
            "reward_quantity",
            "leader",
            "co_leader",
            "timestamp",
        ])
        return ws, True


def get_faction_basic(faction_id: int, torn_key: str, cache: dict) -> dict:

    if faction_id not in cache:
        cache[faction_id] = safe_get(
            f"https://api.torn.com/v2/faction/{faction_id}/basic",
            torn_key
        )["basic"]
    return cache[faction_id]


def get_user_name(user_id: int | None, torn_key: str, cache: dict[int, str]) -> str:

    if not user_id:
        return "vacant"

    if user_id not in cache:
        profile = safe_get(
            f"https://api.torn.com/v2/user/{user_id}/basic?striptags=true",
            torn_key
        )["profile"]
        cache[user_id] = profile["name"]
    return cache[user_id]


def log_event(spreadsheet, event, faction_name, racket_name, territory):
    ws_logs = spreadsheet.worksheet("Logs")
    ws_logs.append_row([
        datetime_to_excel_date(datetime.now(timezone.utc)),
        event,
        faction_name,
        racket_name,
        territory,
    ])

def build_and_send_alert(
    sms_account: dict,
    computer: str,
    *,
    event: str,
    territory: str,
    racket_name: str | None = None,
    faction_name: str | None = None,
    level: int | None = None,
):

    lines = ["ALERT from rackets monitoring"]
    match event:
        case "spawned":
            lines.append("New racket spawned:")
        case "level_up":
            lines.append("Racket level increased:")
        case "level_down":
            lines.append("Racket level decreased:")
        case "disappeared":
            lines.append("Racket has disappeared:")

    lines.append(f"{racket_name}")
    lines.append(f"Level {level}")
    lines.append(f"Faction {faction_name}")
    lines.append(f"Territory {territory}")
    lines.append(f"Report by {computer}")
    # if last_snapshot:
    #     lines.append("Last known state:")
    #     lines.append(str(last_snapshot))

    message = "\n".join(lines)
    send_sms(message = message, sms_account = sms_account)


def notify_and_log_event(spreadsheet,
                         sms_account,
                         computer,
                         *,
                         event,
                         territory,
                         racket_name,
                         faction_name,
                         level
):

    build_and_send_alert(
        sms_account,
        computer,
        event=event,
        territory=territory,
        racket_name=racket_name,
        faction_name=faction_name,
        level=level,
    )
    log_event(spreadsheet, event, faction_name, racket_name, territory)


def update_racket(
    spreadsheet,
    computer : str,
    sms_account: dict,
    territory: str,
    racket: dict,
    torn_key: str,
    faction_cache: dict,
    user_cache: dict
):

    ws, is_new = get_or_create_racket_sheet(spreadsheet, territory)
    records = ws.get_all_records()
    last_snapshot = records[-1] if records else None

    if last_snapshot and last_snapshot["timestamp"] == racket["changed_at"]:
        return  # no evolution !

    faction = get_faction_basic(racket["faction_id"], torn_key, faction_cache)
    leader = get_user_name(faction.get("leader_id"), torn_key, user_cache)
    co_leader = get_user_name(faction.get("co_leader_id"), torn_key, user_cache)

    ws.append_row([
        timestamp_to_excel_date(racket["created_at"]),
        timestamp_to_excel_date(racket["changed_at"]),
        faction["name"],
        racket["faction_id"],
        racket["name"],
        racket["level"],
        racket["description"],
        racket["reward"]["type"],
        racket["reward"]["id"],
        racket["reward"]["quantity"],
        leader,
        co_leader,
        racket["changed_at"],
    ])

    if is_new:
        notify_and_log_event(
            spreadsheet,
            sms_account,
            computer,
            event="spawned",
            territory=territory,
            racket_name=racket["name"],
            faction_name=faction["name"],
            level=racket["level"],
        )
        return

    if not last_snapshot:
        return  # sécurité, ne devrait plus arriver

    delta = racket["level"] - int(last_snapshot["level"])

    notify_and_log_event(
        spreadsheet,
        sms_account,
        computer,
        event="level_up" if delta > 0 else "level_down",
        territory=racket["territory"],
        racket_name=racket["name"],
        faction_name=faction["name"],
        level=racket["level"],
    )

def main():
    config = load_config()
    runtime_data = config["runtime_data"]
    service_file = config["data_path"] + runtime_data["google"]["service_account_file"]
    computer = config["computer"]

    torn_key = runtime_data["torn_keys"]["Kwartz"]
    spreadsheet_id = runtime_data["spreadsheet_ids"]["rackets_monitoring"]
    sms_account = runtime_data["sms_account"]

    gs_client = gspread.service_account(filename=service_file)
    spreadsheet = gs_client.open_by_key(spreadsheet_id)

    faction_ids = {27223, 14078, 33241}

    rackets = get_tracked_rackets(torn_key, faction_ids)

    detect_disappeared_rackets(spreadsheet, sms_account, computer, set(rackets.keys()))

    faction_cache = {}
    user_cache = {}

    for territory, racket in rackets.items():
        update_racket(
            spreadsheet,
            computer,
            sms_account,
            territory,
            racket,
            torn_key,
            faction_cache,
            user_cache,
        )

    ws_update = spreadsheet.worksheet("Last update")
    ws_update.update_cell(1, 1, f"Updated by {computer}")
    ws_update.update_cell(1, 2, datetime_to_excel_date(datetime.now(timezone.utc)))

# updated with runtime_data
if __name__ == "__main__":
    main()