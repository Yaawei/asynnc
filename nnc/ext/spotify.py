import datetime
import collections
import re

import aiohttp

from nnc.core.plugin import regex


current_token = collections.defaultdict(str)


async def request_authorization():
    async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            auth=aiohttp.BasicAuth("57a6be682bbf4be5be98c0d01e68049d", "1459804e285c4a8e9429c6154672941d"),
            data={"grant_type": "client_credentials"}) as resp:
        reply = await resp.json()
        token = reply['access_token']
        expiration = datetime.datetime.now() + datetime.timedelta(seconds=reply['expires_in'])
        current_token["token"] = token
        current_token["expiration"] = expiration


async def get_info(subject, subject_id, token=None, expiration=None):
    if not token or not expiration or expiration < datetime.datetime.now():
        await request_authorization()

    url = "https://api.spotify.com/v1/%s/%s" % (subject, subject_id)
    async with aiohttp.request(
        "GET",
        url,
        headers={"Authorization": "Bearer %s" % current_token["token"]}
    ) as resp:
        return await resp.json()


@regex("spotify:(album|track|artist):\w{22}")
async def describe_subject(bot, msg):
    message = msg.params[-1]
    pat = "spotify:(track|album|artist):(\w{22})"
    uri = re.search(pat, message)
    subject = "%ss" % uri.group(1)

    data = await get_info(
        subject=subject,
        subject_id=uri.group(2),
        token=current_token["token"] or None,
        expiration=current_token["expiration"] or None,
    )

    name = data["name"]

    if subject == "tracks":
        author = data["artists"][0]["name"]
        length = datetime.timedelta(seconds=data["duration_ms"] // 1000)
        bot.reply(msg, "SPOTIFY: \"%s\" (%s) by %s" % (name, str(length), author))

    if subject == "albums":
        author = data["artists"][0]["name"]
        release_date = data["release_date"]
        bot.reply(msg, "SPOTIFY: \"%s\" (%s) by %s" % (name, release_date, author))

    if subject == "artists":
        bot.reply(msg, "SPOTIFY: %s" % name)
