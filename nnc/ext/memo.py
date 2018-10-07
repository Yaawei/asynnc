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
    recipient = contents[1]
    message = contents[2]
    sender = msg.nick
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
    bot.reply(msg, 'done')


def send_memo(bot, memo):
    if memo.recipient not in bot.channels[memo.channel] or memo.delivery_time > datetime.datetime.now():
        bot.loop.call_later(60, send_memo, bot, memo)
    else:
        bot.say(memo.channel,
                '%s, here is message for you from %s sent at %s: %s' % (
                    memo.recipient,
                    memo.sender,
                    memo.sent_at,
                    memo.message
                 ))
        asyncio.create_task(bot.objects.delete(memo))


@onload
async def load_memo_from_db(bot):
    memo_qs = await bot.objects.execute(Memo.select())
    for memo in memo_qs:
        bot.loop.call_soon(send_memo, bot, memo)
