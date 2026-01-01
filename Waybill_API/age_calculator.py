from datetime import datetime,timedelta,timezone

def Age_calculator(date_str: str) -> float:
            """Ensure the string ends with 'CST' and split it off"""
            parts = date_str.strip().rsplit(" ", 1)
            if len(parts) != 2 or parts[1].upper() != "CST":
                return None
            dt_part = parts[0]  # 'dd-mon-yyyy HH:MM:SS'

            # Parse 'dd-mon-yyyy HH:MM:SS' allowing case-insensitive month
            try:
                date_section, time_section = dt_part.split(" ", 1)
                day_str, mon_str, year_str = "","",""
                if "-" in date_section:
                    day_str, mon_str, year_str = date_section.split("-")
                if ":" in date_section:
                    day_str, mon_str, year_str = date_section.split(":")
                if "/" in date_section:
                    day_str, mon_str, year_str = date_section.split("/")
                mon_norm = mon_str.title()  # e.g., 'dec' -> 'Dec', 'DEC' -> 'Dec'
                normalized = f"{day_str}-{mon_norm}-{year_str} {time_section}"
                naive = datetime.strptime(normalized, "%d-%b-%Y %H:%M:%S")
            except Exception as e:
                raise ValueError(f"Failed to parse date/time: {e}")

            # Fixed CST: UTC−06:00 (no DST)
            FIXED_CST = timezone(timedelta(hours=-6))
            cst_dt = naive.replace(tzinfo=FIXED_CST)

            # Compute difference in UTC for consistency
            now_utc = datetime.now(timezone.utc)
            delta = now_utc - cst_dt.astimezone(timezone.utc)

            # Convert seconds to days
            return int(delta.total_seconds() / 86400.0)
