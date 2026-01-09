from datetime import datetime
from zoneinfo import ZoneInfo

def Age_calculator(timestamp_str):
    """
    Returns days between today (CST) and input string.
    Returns 0 for None, empty, or invalid formats.
    """
    # 1. Validation for None or Empty
    if not timestamp_str or not isinstance(timestamp_str, str):
        return None
        
    # 2. Setup Central Time (Handles both CST/CDT)
    # Using 'US/Central' as it is highly compatible across systems
    try:
        tz_cst = ZoneInfo("US/Central")
    except Exception:
        # Fallback if tzdata is still missing in your environment
        return 0
        
    current_date_cst = datetime.now(tz_cst).date()

    # 3. Handle "yesterday" shortcut
    clean_val = timestamp_str.strip().lower()
    if clean_val == "yesterday":
        return 1

    try:
        # 4. Parse specific format: "DD-MON-YYYY Hrs:Min:Sec CST"
        # We strip the manual " CST" suffix to use strptime cleanly
        raw_str = timestamp_str.replace(" CST", "").strip()
        parsed_dt = datetime.strptime(raw_str, "%d-%b-%Y %H:%M:%S")
        
        # 5. Calculate date-only difference
        input_date = parsed_dt.date()
        delta = current_date_cst - input_date
        
        return delta.days

    except (ValueError, TypeError):
        # Return 0 if the format is incorrect
        return 0
