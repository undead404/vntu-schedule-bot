import datetime
import json
from pprint import pprint
import re
import time
from decouple import config
import telepot
import telepot.loop
from root import get_announcement, get_day_schedule, load_schedule
API_TOKEN = config("API_TOKEN")
BOT = telepot.Bot(API_TOKEN)
DATE_FULL_RE = re.compile("([0123]?\d)\.([01]?\d)\.(\d{4})")
DATE_SHORT_RE = re.compile("([0123]?\d)\.([01]?\d)")
SCHEDULE_END = datetime.datetime.strptime(
    config("SCHEDULE_END"), "%d.%m.%Y").date()
SCHEDULE_START = datetime.datetime.strptime(
    config("SCHEDULE_START"), "%d.%m.%Y").date()


class Chat(object):
    __cache = {}
    __id = None
    __next_handlers = None
    __subgroup_number = None

    def __init__(self, id_):
        self.__id = id_
        if self.__subgroup_number is None:
            with open("subgroups.json") as subgroups_file:
                self.__subgroup_number = json.load(
                    subgroups_file).get(str(self.__id))
        if self.__subgroup_number is None:
            self.__next_handlers = (self.greet, self.ask_about_subgroup)
        else:
            self.__next_handlers = (self.greet, self.sendSchedule)

    def ask_about_subgroup(self, message):
        BOT.sendMessage(self.__id, "З якої ти підгрупи?")
        self.__next_handlers = (self.save_subgroup, )

    def ask_to_excuse(self, message):
        BOT.sendMessage(self.__id, "Вибач, я тебе не зрозумів :(")

    def change_subgroup(self, subgroup_number):
        assert subgroup_number in [1, 2]
        self.__subgroup_number = subgroup_number
        with open("subgroups.json") as subgroups_file:
            subgroups = json.load(subgroups_file)
        subgroups[self.__id] = self.__subgroup_number
        with open("subgroups.json", "w") as subgroups_file:
            json.dump(subgroups, subgroups_file)

    def greet(self, message):
        BOT.sendMessage(
            self.__id, "Привіт!) Це бот розкладу занять академічної групи 1ПІ-17м ВНТУ.")

    @classmethod
    def get(cls, id_):
        chat = cls.__cache.get(id_)
        if chat is None:
            chat = cls(id_)
            cls.__cache[id_] = chat
        return chat

    def handle(self, message):
        for handler in self.__next_handlers:
            handler(message)

    def okay(self, message):
        BOT.sendMessage(
            self.__id, "Ура всім нам!) який розклад хочеш отримати? Сьогоднішній, завтрашній, вчорашній або у форматі 01.01.1970.\n\nЩоб змінити підгрупу, введи '/changeSubgroup 1' ('зубенко') чи '/changeSubgroup 2' ('абрамович')")
        self.__next_handlers = (self.sendSchedule, )

    def save_subgroup(self, message):
        try:
            subgroup_number = int(message["text"])
            if subgroup_number not in [1, 2]:
                raise ValueError("wrong substring number.")
            self.__subgroup_number = subgroup_number
            with open("subgroups.json") as subgroups_file:
                subgroups = json.load(subgroups_file)
            subgroups[self.__id] = self.__subgroup_number
            with open("subgroups.json", "w") as subgroups_file:
                json.dump(subgroups, subgroups_file)
            self.okay(message)
        except ValueError:
            self.ask_to_excuse(message)
            self.ask_about_subgroup(message)

    def sendHelp(self, message):
        BOT.sendMessage(self.__id, """Нагадую! Це бот розкладу занять академічної групи 1ПІ-17м ВНТУ.
        Варіанти використання:
        * Сьогодні
        * Завтра
        * Післязавтра
        * Вчора
        * Позавчора
        * 1.12.2017
        * 2.10.2017
        
        Щоб змінити підгрупу, введи `/changeSubgroup 1` або `/changeSubgroup 2`""")

    def sendSchedule(self, message):
        try:
            question = message["text"].lower().strip(" .?")
            if question.startswith("/changeSubgroup "):
                subgroup_number = int(question.split(" ")[1])
                self.change_subgroup(subgroup_number)
                self.okay(message)
            elif question.startswith("/help"):
                self.sendHelp(message)
                self.okay(message)
            else:
                date = guess_date(question)
                if date < SCHEDULE_START or date >= SCHEDULE_END:
                    BOT.sendMessage(self.__id, date.strftime("%d.%m.%Y") + "\n" + "Вибач. У мене лише розклад 1 семестру магістратури. Решту життя плануй самостійно.")
                else:
                    schedule = load_schedule(filename="schedule.json")[
                        "schedules"][self.__subgroup_number - 1]
                    today_schedule = get_day_schedule(date, schedule)
                    announcement = get_announcement(today_schedule)
                    BOT.sendMessage(self.__id, date.strftime("%d.%m.%Y") + "\n" + announcement)
        except ValueError:
            self.ask_to_excuse(message)


def guess_date(text):
    text = text.lower()
    if text.startswith("після"):
        return guess_date(text[len("після"):]) + datetime.timedelta(days=1)
    elif text.startswith("поза"):
        return guess_date(text[len("поза"):]) - datetime.timedelta(days=1)
    elif "сьогодні" in text or "нині" in text:
        return datetime.datetime.now().date()
    elif "вчора" in text or "учора" in text:
        return datetime.datetime.now().date() - datetime.timedelta(days=1)
    elif "завтра" in text:
        return datetime.datetime.now().date() + datetime.timedelta(days=1)
    else:
        result = re.search(DATE_FULL_RE, text)
        # result = DATE_FULL_RE.match(text)
        if result is not None:
            day = int(result.group(1))
            month = int(result.group(2))
            year = int(result.group(3))
            return datetime.date(year, month, day)
        else:
            result = re.search(DATE_SHORT_RE, text)
            # result = DATE_SHORT_RE.match(text)
            if result is not None:
                day = int(result.group(1))
                month = int(result.group(2))
                year = datetime.datetime.now().date().year
                return datetime.date(year, month, day)
            else:
                raise ValueError("Wrong date format")


def handle(message):
    pprint(message)
    chat_id = message["chat"]["id"]
    if chat_id > 0:
        chat = Chat.get(chat_id)
        chat.handle(message)


if __name__ == "__main__":
    telepot.loop.MessageLoop(BOT, handle).run_as_thread()
    while True:
        time.sleep(10)
