import datetime
from datetime import timedelta


def YesterdayPrefix():
    # today_date = datetime.date.today()
    todayDate = datetime.datetime(2022, 4, 30)
    yesterday = todayDate - timedelta(days=1)
    yesterdayPrefix = yesterday.strftime("%Y%m%d")
    return yesterdayPrefix