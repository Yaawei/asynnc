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
async def memo(bot, msg):
    contents = msg.params[-1].split(' ', 2)
    recipient = contents[1]
    message = contents[2]
    sender = msg.nick
    sent_at = datetime.datetime.now()
    channel = msg.channel

    memo_obj = await bot.objects.create(
        Memo,
        message=message,
        recipient=recipient,
        sender=sender,
        sent_at=sent_at,
        delivery_time=sent_at,
        channel=channel,
    )
    await memo_loop(bot, memo_obj)
    bot.reply(msg, 'done')


# @cmd('remind')
# def remind(bot, msg):
#     contents = msg.params[-1].split(' ', 3)
#     recipient = contents[1]
#     delivery_time = contents[2]
#     message = contents[3]
#     sender = msg.nick
#     sent_at = datetime.datetime.now()


async def memo_loop(bot, memo_obj):
    while True:
        if memo_obj.recipient in bot.channels[memo_obj.channel]:
            if memo_obj.delivery_time <= datetime.datetime.now():
                bot.say(memo_obj.channel,
                        '%s, here is message for you from %s sent at %s: %s' % (
                         memo_obj.recipient,
                         memo_obj.sender,
                         memo_obj.sent_at,
                         memo_obj.message
                         ))
                await bot.objects.delete(memo_obj)
                break
        await asyncio.sleep(60)


@onload
async def load_memo_from_db(bot):
    memo_qs = await bot.objects.execute(Memo.select())
    for memo_obj in memo_qs:
        asyncio.create_task(memo_loop(bot, memo_obj))


