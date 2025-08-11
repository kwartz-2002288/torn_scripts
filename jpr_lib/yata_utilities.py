import json

def get_yata_targets(path):
    """"
    get the targets exported by YATA in path/target_list.json and load in a dictionary
    """
    with open(path+'target_list.json','r') as f:
        return json.load(f)