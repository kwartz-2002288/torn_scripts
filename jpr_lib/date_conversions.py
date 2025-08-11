from datetime import datetime, timezone

def python_date_to_excel_number(date):
    """
    Convert a python date (utc datetime format)
    to a number representing
    a date in a Google sheet
    """
    # Define the reference date for Google Sheets (December 30, 1899)
    reference_date = datetime(1899, 12, 30, tzinfo=timezone.utc)
    # Calculate the difference in days
    days_difference = (date - reference_date).days
    # Calculate the fraction of the day
    fraction_of_day = (date - datetime(date.year, date.month, date.day,
        tzinfo=timezone.utc)).total_seconds() / 86400.0  # 86400 seconds in a day
    # Calculate the total number
    date_number = days_difference + fraction_of_day
    return date_number
