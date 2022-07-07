# Gets path for yesterday depending uppon the server deployment

import datetime
from datetime import timedelta
from pathlib import Path

from Utils.YesterdayPrefix import YesterdayPrefix

def GetPathForLogs(currentSite, logFile):
    if currentSite == "Beth" and logFile == "master_wireless":
        yesterday_prefix = YesterdayPrefix
        currentPath = Path("/logs/wireless/" + yesterday_prefix + "/master_wireless.log.gz")
    elif currentSite == "beth" and logFile == "DiscoReport":
        today_date = datetime.date.today()
        yesterday = today_date - timedelta(days=1)
        yesterday_prefix = yesterday.strftime("%Y-%m-%d")
        currentPath = Path("/mnt/sre01/RoverServices/" + yesterday_prefix + "/")
    return currentPath