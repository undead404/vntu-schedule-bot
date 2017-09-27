#!./venv/bin/python3

from root import *
from pprint import pprint
from datetime import datetime

date = datetime(year=2017, month=10, day=14).date()
data = load_schedule()
for schedule in data["schedules"]:
    channel_id = int(schedule["channelId"])
    today_schedule = get_day_schedule(date, schedule)
    announcement = get_announcement(today_schedule)
    print(announcement)
