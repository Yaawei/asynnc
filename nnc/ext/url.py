import collections
import datetime
import re
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from isodate import parse_duration

from nnc.core.plugin import regex


spotify_token = collections.defaultdict(str)


@regex("https?:\/\/\w+([\-\.]?\w+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$")
async def dispatch_url(bot, msg):
    message = msg.params[-1]
    pat = re.compile(r"https?:\/\/\w+([\-\.]?\w+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$")
    url = re.search(pat, message)
    url_data = urlparse(url.group())

    if url_data.netloc == "www.youtube.com" and url_data.path == "/watch":
        vid_id = url_data.query[2:13]
        await describe_yt_video(bot, msg, vid_id)

    elif url_data.netloc == "youtu.be":
        vid_id = url_data.path[1:12]
        await describe_yt_video(bot, msg, vid_id)

    else:
        await describe_basic_url(bot, msg, url.group())


async def describe_basic_url(bot, msg, url):
    async with bot.session.get(url) as resp:
        soup = BeautifulSoup(await resp.text(), "html.parser")
        title = soup.title.get_text()
        bot.reply(msg, "URL: %s" % title)


async def describe_yt_video(bot, msg, vid_id):
    async with bot.session.get(
            "https://www.googleapis.com/youtube/v3/videos/?",
            params={
                "part": "snippet,contentDetails",
                "id": vid_id,
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


@regex("spotify:(album|track|artist):\w{22}")
async def describe_spotify_url(bot, msg):
    message = msg.params[-1]
    pat = re.compile(r"spotify:(album|track|artist):(\w{22})")
    url = re.search(pat, message)
    subject = "%ss" % url.group(1)

    data = await get_spotify_info(
        bot=bot,
        client_id=bot.config.spotify_client_id,
        client_secret=bot.config.spotify_client_secret,
        subject=subject,
        subject_id=url.group(2),
        token=spotify_token["token"] or None,
        expiration=spotify_token["expiration"] or None,
    )

    name = data["name"]
    if subject == "tracks":
        author = data["artists"][0]["name"]
        length = datetime.timedelta(seconds=data["duration_ms"] // 1000)
        bot.reply(msg, 'SPOTIFY: "%s" (%s) by %s' % (name, str(length), author))

    elif subject == "albums":
        author = data["artists"][0]["name"]
        release_date = data["release_date"]
        bot.reply(msg, 'SPOTIFY: "%s" (%s) by %s' % (name, release_date, author))

    elif subject == "artists":
        bot.reply(msg, "SPOTIFY: %s" % name)


async def get_spotify_info(
        bot, client_id, client_secret, subject, subject_id, token=None, expiration=None
):
    if not token or not expiration or expiration < datetime.datetime.now():
        await request_spotify_authorization(bot, client_id, client_secret)

    url = "https://api.spotify.com/v1/%s/%s" % (subject, subject_id)
    async with bot.session.get(url, headers={"Authorization": "Bearer %s" % spotify_token["token"]}) as resp:
        return await resp.json()


async def request_spotify_authorization(bot, client_id, client_secret):
    async with bot.session.post(
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

