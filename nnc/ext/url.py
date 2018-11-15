import collections
import datetime
import re

import aiohttp
from bs4 import BeautifulSoup
from isodate import parse_duration

from nnc.core.plugin import regex


# SPOTIFY
spotify_token = collections.defaultdict(str)


async def request_spotify_authorization(client_id, client_secret):
    async with aiohttp.request(
        "POST",
        "https://accounts.spotify.com/api/token",
        auth=aiohttp.BasicAuth(client_id, client_secret),
        data={"grant_type": "client_credentials"},
    ) as resp:
        reply = await resp.json()
        token = reply["access_token"]
        expiration = datetime.datetime.now() + datetime.timedelta(
            seconds=reply["expires_in"]
        )
        spotify_token["token"] = token
        spotify_token["expiration"] = expiration


@regex("spotify:(album|track|artist):\w{22}")
async def describe_spotify_url(bot, msg):
    message = msg.params[-1]
    pat = "spotify:(track|album|artist):(\w{22})"
    uri = re.search(pat, message)
    subject = "%ss" % uri.group(1)

    data = await get_info(
        client_id=bot.config.spotify_client_id,
        client_secret=bot.config.spotify_client_secret,
        subject=subject,
        subject_id=uri.group(2),
        token=spotify_token["token"] or None,
        expiration=spotify_token["expiration"] or None,
    )

    name = data["name"]

    if subject == "tracks":
        author = data["artists"][0]["name"]
        length = datetime.timedelta(seconds=data["duration_ms"] // 1000)
        bot.reply(msg, 'SPOTIFY: "%s" (%s) by %s' % (name, str(length), author))

    if subject == "albums":
        author = data["artists"][0]["name"]
        release_date = data["release_date"]
        bot.reply(msg, 'SPOTIFY: "%s" (%s) by %s' % (name, release_date, author))

    if subject == "artists":
        bot.reply(msg, "SPOTIFY: %s" % name)


async def get_info(
    client_id, client_secret, subject, subject_id, token=None, expiration=None
):
    if not token or not expiration or expiration < datetime.datetime.now():
        await request_spotify_authorization(client_id, client_secret)

    url = "https://api.spotify.com/v1/%s/%s" % (subject, subject_id)
    async with aiohttp.request(
        "GET", url, headers={"Authorization": "Bearer %s" % spotify_token["token"]}
    ) as resp:
        return await resp.json()


# YOUTUBE
@regex("youtu\.be/([a-zA-Z0-9_-]{11})")
@regex("youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})")
async def describe_yt_video(bot, msg):
    message = msg.params[-1]
    link_pattern1 = "youtu\.be/([a-zA-Z0-9_-]{11})"
    link_pattern2 = "youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"
    video_id = re.search(link_pattern1, message) or re.search(link_pattern2, message)
    if video_id:
        async with aiohttp.request(
            "GET",
            "https://www.googleapis.com/youtube/v3/videos/?",
            params={
                "part": "snippet,contentDetails",
                "id": video_id.group(1),
                "key": bot.config.yt_api_key,
            },
        ) as resp:
            video_info = await resp.json()
            title = video_info["items"][0]["snippet"]["title"]
            author = video_info["items"][0]["snippet"]["channelTitle"]
            duration = parse_duration(
                video_info["items"][0]["contentDetails"]["duration"]
            )

            bot.reply(msg, "YouTube: %s (%s) by %s" % (title, str(duration), author))


# URLS
session = aiohttp.ClientSession()


@regex(
    "(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"
)
async def describe_site(bot, msg):
    message = msg.params[-1]
    pat = re.compile(
        r"""
    (http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)   # base url    
    [a-z0-9]+([\-\.]+[a-z0-9]+)*\.[a-z]{2,5}                # base url
    (:[0-9]{1,5})?(\/.*)?$                                  # path
    """,
        re.X,
    )
    murl = re.match(pat, message)
    if re.search("youtu\.be/([a-zA-Z0-9_-]{11})", murl.group()) or re.search(
        "youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})", murl.group()
    ):
        return
    async with session.get(murl.group()) as resp:
        soup = BeautifulSoup(await resp.text(), "html.parser")
        title = soup.title.get_text()
        bot.reply(msg, "URL: %s" % title)
