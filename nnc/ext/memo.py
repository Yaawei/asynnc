import datetime
import asyncio
import re

import peewee

from nnc.core.plugin import cmd, onload
from nnc.core.db import BaseModel


class Memo(BaseModel):
    message = peewee.TextField()
    recipient = peewee.CharField()
    sender = peewee.CharField()
    sent_at = peewee.DateTimeField()
    delivery_time = peewee.DateTimeField()
    channel = peewee.CharField()


@cmd("memo")
async def save_memo(bot, msg):
    contents = msg.params[-1].split(" ", 2)
    if len(contents) != 3:
        bot.reply(
            msg,
            "Wrong number of arguments. The correct format is - "
            "!memo <recipient>(e.g. JohnDoe) <message>",
        )
        return

    recipient = contents[1]
    message = contents[2]
    sender = msg.nick.rstrip("_")
    sent_at = datetime.datetime.now()
    channel = msg.channel

    memo = await bot.objects.create(
        Memo,
        message=message,
        recipient=recipient,
        sender=sender,
        sent_at=sent_at,
        delivery_time=sent_at,
        channel=channel,
    )
    bot.loop.call_soon(send_memo, bot, memo)
    bot.reply(msg, "Successfully saved memo for %s" % recipient)


@cmd("remind")
async def save_remind(bot, msg):
    contents = msg.params[-1].split(" ", 3)
    if len(contents) != 4:
        bot.reply(
            msg,
            "Wrong number of arguments. The correct format is - "
            "!remind <recipient>(e.g. JohnDoe) <time>(e.g. 2d4h15m35s) <message>",
        )
        return

    recipient = contents[1]
    message = contents[3]
    delivery_time, delivery_time_delta = parse_time(contents[2])
    sender = msg.nick.rstrip("_")
    sent_at = datetime.datetime.now()
    channel = msg.channel

    memo = await bot.objects.create(
        Memo,
        message=message,
        recipient=recipient,
        sender=sender,
        sent_at=sent_at,
        delivery_time=delivery_time,
        channel=channel,
    )
    bot.loop.call_later(delivery_time_delta.total_seconds(), send_memo, bot, memo)
    bot.reply(
        msg,
        "Reminder for %s set at %s"
        % (recipient, delivery_time.strftime("%H:%M:%S, %e %b %Y")),
    )


def send_memo(bot, memo):
    stripped_users = [user.lower().strip("@_") for user in bot.channels[memo.channel]]
    if (
        memo.recipient.lower().strip("@_") not in stripped_users
        or memo.delivery_time > datetime.datetime.now()
    ):
        bot.loop.call_later(60, send_memo, bot, memo)
    else:
        bot.say(
            memo.channel,
            "%s (to %s, from %s on %s)"
            % (
                memo.message,
                memo.recipient,
                memo.sender,
                memo.sent_at.strftime("%H:%M, %e %b %Y"),
            ),
        )
        asyncio.create_task(bot.objects.delete(memo))


@onload
async def load_memo_from_db(bot):
    memo_qs = await bot.objects.execute(Memo.select())
    for memo in memo_qs:
        bot.loop.call_later(30, send_memo, bot, memo)


def parse_time(time_str):
    pat = re.compile(r"""
        (?:(?P<days>\d+)d(?:ays?|ni)?)?     
        (?:(?P<hours>\d+)h(?:ours?)?)?
        (?:(?P<minutes>\d+)m(?:inu?t?)?)?
        (?:(?P<seconds>\d+)s(?:e(?:k|c))?)?
        """, re.X)

    mo = re.match(pat, time_str)
    timedict = {k: int(v) for k, v in mo.groupdict().items() if isinstance(v, str)}
    if timedict:
        delivery_time_delta = datetime.timedelta(**timedict)
        delivery_time = datetime.datetime.now() + delivery_time_delta
        return delivery_time, delivery_time_delta
    else:
        delivery_time = datetime.datetime.now()
        delivery_time_delta = datetime.timedelta(0, 0, 0, 0, 0, 0)

        return delivery_time, delivery_time_delta
