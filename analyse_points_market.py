from jpr_lib import load_config, point_value_averaged

# Use "verbose = True" for more information

verbose = True
config = load_config()
torn_key = config["runtime_data"]["torn_keys"]["Kwartz"]
average_value = point_value_averaged(torn_key=torn_key, n_average=10, verbose=verbose)

print(f"\naverage point cost: {int(average_value)} $")
