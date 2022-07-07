import datetime
from datetime import timedelta


def YesterdayPrefix():
    today_date = datetime.date.today()
    yesterday = today_date - timedelta(days=1)
    yesterdayPrefix = yesterday.strftime("%Y%m%d")
    return yesterdayPrefix