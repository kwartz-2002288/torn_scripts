def load_config():
    """
    Load configuration for Torn project scripts.

    legacy=True  -> load old separate JSON files (torn_keys, free_keys, sheet_keys, various_torn_data)
    legacy=False -> load new runtime_data.json (consolidated)
    """
    import os, platform, json

    system = platform.system()
    if system == "Linux":
        home_path = "/home/"
    elif system == "Darwin":
        home_path = "/Users/"
    else:
        raise RuntimeError(f"Unsupported system: {system}")

    computer = os.uname().nodename.removesuffix(".local")
    data_path = os.path.join(home_path, "jpr/torn_data/")
    scripts_path = os.path.join(home_path, "jpr/torn_scripts/")
    runtime_file = os.path.join(data_path, "runtime_data.json")

    with open(runtime_file, "r", encoding="utf-8") as f:
        runtime_data = json.load(f)
    return {
        "system": system,
        "computer": computer,
        "data_path": data_path,
        "scripts_path": scripts_path,
        "runtime_data": runtime_data
    }

