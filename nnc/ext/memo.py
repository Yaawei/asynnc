import datetime
import asyncio

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


@cmd('memo')
async def save_memo(bot, msg):
    contents = msg.params[-1].split(' ', 2)
    if len(contents) == 3:
        recipient = contents[1]
        message = contents[2]
        sender = msg.nick.rstrip('_')
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
        bot.reply(msg, 'successfully saved memo for %s' % recipient)

    else:
        bot.reply(
            msg,
            'Wrong number of arguments. The correct format is - '
            '!memo <recipient>(e.g. JohnDoe) <message>'
        )


@cmd('remind')
async def save_remind(bot, msg):
    contents = msg.params[-1].split(' ', 3)
    if len(contents) == 4:
        recipient = contents[1].lower()
        message = contents[3]
        delivery_time, delivery_time_delta = parse_time(contents[2])
        sender = msg.nick.rstrip('_')
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
        bot.reply(msg, 'reminder for %s set at %s' % (recipient, str(delivery_time)[:-7]))

    else:
        bot.reply(
            msg,
            'Wrong number of arguments. The correct format is - '
            '!remind <recipient>(e.g. JohnDoe) <time>(e.g. 2d,4h,15m,35s) <message>'
        )


def send_memo(bot, memo):
    if memo.recipient not in bot.channels[memo.channel] \
            or memo.delivery_time > datetime.datetime.now():
        bot.loop.call_later(60, send_memo, bot, memo)
    else:
        bot.say(memo.channel,
                '%s (from %s on %s)' % (
                    memo.message,
                    memo.sender,
                    memo.sent_at.strftime("%H:%M, %e %b %Y"),
                 ))
        asyncio.create_task(bot.objects.delete(memo))


@onload
async def load_memo_from_db(bot):
    memo_qs = await bot.objects.execute(Memo.select())
    for memo in memo_qs:
        bot.loop.call_later(30, send_memo, bot, memo)


def parse_time(time_str):
    legal_letters = ['h', 'd', 's', 'm']
    time_split = time_str.split(',')
    times = {x[-1]: int(x[:-1]) for x in time_split
             if x and x[-1] in legal_letters and x[:-1].isdigit()}
    if times:
        for let in legal_letters:
            if let not in times.keys():
                times[let] = 0

        delivery_time_delta = datetime.timedelta(
            days=times['d'], hours=times['h'], minutes=times['m'], seconds=times['s'])
        delivery_time = datetime.datetime.now() + delivery_time_delta

        return delivery_time, delivery_time_delta
    else:
        delivery_time = datetime.datetime.now()
        delivery_time_delta = datetime.timedelta(0, 0, 0, 0, 0, 0)

        return delivery_time, delivery_time_delta
