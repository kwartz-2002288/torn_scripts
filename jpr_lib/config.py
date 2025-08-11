import os
import json
import platform

def load_config():
    """
    Search system and computer name
    Load API keys and sheet keys from JSON files
    Return a config dict
    """
    system = platform.system()
    if system == 'Linux':
        home_path = '/home/'
    elif system == 'Darwin':  # macOS
        home_path = '/Users/'
    else:
        raise Exception(f'Unsupported system: {system}')

    computer = os.uname().nodename.removesuffix(".local")

    data_path = home_path + 'jpr/torn_data/'
    scripts_path = home_path + 'jpr/torn_scripts/'
    with open(data_path + 'torn_keys.json') as f:
        torn_keys = json.load(f)
    with open(data_path + 'free_keys.json') as f:
        free_keys = json.load(f)
    with open(data_path + 'sheet_keys.json') as f:
        sheet_keys = json.load(f)

    return {
        'system': system,
        'computer': computer,
        'data_path': data_path,
        'scripts_path': scripts_path,
        'torn_keys': torn_keys,
        'free_keys': free_keys,
        'sheet_keys': sheet_keys
    }
