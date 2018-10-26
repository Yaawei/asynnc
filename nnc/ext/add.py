from datetime import datetime

import peewee

from nnc.core.bot import irc
from nnc.core.plugin import cmd, CMD_HANDLERS
from nnc.core.db import BaseModel


class Add(BaseModel):
    keyword = peewee.CharField()
    content = peewee.TextField()
    date = peewee.DateTimeField()


@cmd("add")
async def save_entry(bot, msg):
    msg_contents = msg.params[-1].split(' ', 2)
    if len(msg_contents) == 3:
        keyword = msg_contents[1]
        content = msg_contents[2]
        date = datetime.now()

        if keyword in CMD_HANDLERS.keys():
            bot.reply(msg, "Can't assign entry to this keyword: %s" % keyword)

        else:
            await bot.objects.create(
                Add,
                keyword=keyword,
                content=content,
                date=date,
            )
            bot.reply(msg, 'successfully added entry')
    else:
        bot.reply(
            msg,
            "Wrong number of arguments. The correct format is - "
            "!add <keyword>(e.g. phones) <entry>(e.g. John: 123-456-789)"
        )


@irc(cmd="PRIVMSG")
async def parse_privmsg(bot, msg):
    text = msg.params[-1]
    if text.startswith(bot.config.cmd_trigger):
        keyword = text[1:].split(" ", 1)[0]
        entries = await bot.objects.prefetch(Add.select().where(Add.keyword == keyword))
        contents = []
        for entry in entries:
            contents.append(entry.content)
        # uncomment when send_many is merged into master
        # send_many(target=msg.channel, messages=contents)
