from jpr_lib import timestamp_to_str_date, timestamp_to_excel_date

# def timestamp_to_str_date(ts: int, date_format="%Y-%m-%d %H:%M:%S")

ts = 1767918855
print(timestamp_to_str_date(ts, date_format="%Y-%m-%d %H:%M:%S"))
print(f"timestamp: {ts} -> {timestamp_to_str_date(ts)}")
print(f"timestamp: {ts} -> excel time: {timestamp_to_excel_date(ts)}")