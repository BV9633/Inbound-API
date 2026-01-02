from datetime import datetime,timedelta,timezone

def get_timestamp():
    CST=timezone(timedelta(hours=-6))
    now=datetime.now(CST)
    mon=now.strftime("%b").upper()
    time= f"{now:%d}-{mon}-{now:%Y} {now:%H}:{now:%M}:{now:%S} CST"
    return time