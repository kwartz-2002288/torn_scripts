import os
import platform
import json
import subprocess

def load_config():
    """
    Load configuration for Torn project scripts.
    """
    system = platform.system()

    if system == "Linux":
        home_path = "/home/"
        computer = os.uname().nodename

    elif system == "Darwin":
        home_path = "/Users/"
        computer = subprocess.check_output(
            ["scutil", "--get", "ComputerName"],
            text=True
        ).strip()

    else:
        raise RuntimeError(f"Unsupported system: {system}")

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