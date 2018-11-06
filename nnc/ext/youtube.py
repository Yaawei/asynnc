import asyncio
import json
import re

import aiohttp

from nnc.core.plugin import regex


@regex("youtu\.be/([a-zA-Z0-9_-]{11})")
@regex("youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})")
async def dispatch_msg(bot, msg):
    message = msg.params[-1]
    link_pattern1 = "youtu\.be/([a-zA-Z0-9_-]{11})"
    link_pattern2 = "youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"
    video_id = re.search(link_pattern1, message) or re.search(link_pattern2, message)
    if video_id:
        async with aiohttp.request(
            "GET",
            "https://www.googleapis.com/youtube/v3/videos/?",
            params={
                "part": "snippet%2CcontentDetails",
                "id": video_id.group(1),
                "key": bot.config.yt_api_key,
            },
        ) as resp:
            video_info = json.loads(await resp.text())
            title = video_info["items"][0]["snippet"]["title"]
            author = video_info["items"][0]["snippet"]["channelTitle"]
            duration = video_info["items"][0]["contentDetails"]["duration"].lstrip("PT")
            bot.reply(msg, "%s (%s) by %s" % (title, duration, author))
