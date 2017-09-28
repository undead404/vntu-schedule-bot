#!/home/undead404/vntu-schedule-bot/venv/bin/python3
"""
acquiring today's schedules and sending it to channels
"""
from datetime import datetime
import json
from decouple import config
import telepot

# ANCHOR_DATE is a date of some Monday in an odd week
ANCHOR_DATE = datetime.strptime(config("ANCHOR_DATE"), "%d.%m.%Y").date()
BOT = telepot.Bot(config("API_TOKEN"))
DAYS_IN_WEEK = 7
ODD_WEEK = 0
EVEN_WEEK = 1


def get_announcement(day_schedule):
    """ returns announcement message from certain day's schedule """
    if not day_schedule:
        return "Приємного відпочинку!"
    lessons_announcements = []
    for i, lesson in enumerate(day_schedule):
        if lesson is None:
            lessons_announcements.append("{num}. ВІКНО".format(num=i + 1))
        else:
            lessons_announcements.append(
                "{num}. {room}: {subject} ({teacher}) {type}".format(num=i + 1, **lesson))
    return "\n".join(lessons_announcements)


def get_day_schedule(date, schedule):
    """ returns certain day's schedule """
    try:
        weekday_schedule = schedule["schedule"][date.weekday()]
    except IndexError:
        return []
    ODDITY_EVENNESS = get_oddity_evenness(date)
    day_schedule = []
    for lesson in weekday_schedule:
        if isinstance(lesson, list):
            lesson = lesson[ODDITY_EVENNESS]
        day_schedule.append(lesson)
    day_date_str = date.strftime("%d.%m.%Y")
    if day_date_str in schedule["specialCases"]:
        for lesson_num in schedule["specialCases"][day_date_str]:
            while len(day_schedule) < int(lesson_num):
                day_schedule.append(None)
            day_schedule[int(
                lesson_num) - 1] = schedule["specialCases"][day_date_str][lesson_num]
    return day_schedule


def get_oddity_evenness(date):
    """ returns EVEN_WEEK if a date's week is even and ODD_WEEK if a week is odd."""
    return EVEN_WEEK if (date - ANCHOR_DATE).days // DAYS_IN_WEEK % 2 else ODD_WEEK


def load_schedule(filename="/home/undead404/vntu-schedule-bot/schedule.json"):
    """ loading schedule data from a file """
    with open(filename) as infile:
        return json.load(infile)


if __name__ == "__main__":
    TODAY = datetime.now().date()
    data = load_schedule()
    for schedule in data["schedules"]:
        channel_id = int(schedule["channelId"])
        today_schedule = get_day_schedule(TODAY, schedule)
        announcement = get_announcement(today_schedule)
        BOT.sendMessage(channel_id, announcement)
