import re

import aiohttp

from nnc.core.plugin import regex, cmd


@regex("youtu\.be/([a-zA-Z0-9_-]{11})")
@regex("youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})")
async def describe_video(bot, msg):
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
            duration = video_info["items"][0]["contentDetails"]["duration"].lstrip("PT")

            bot.reply(msg, "%s (%s) by %s" % (title, duration, author))


@cmd("yt")
async def youtube_search(bot, msg):
    results_count = 10
    message = msg.params[-1]
    search_words = message.split(" ", 1)
    if len(search_words) != 2:
        bot.reply(
            msg,
            "Not enough arguments. "
            "The correct format is %syt <search words>"
            "(e.g. %syt timecop1983 night drive full album)"
            % (bot.config.cmd_trigger, bot.config.cmd_trigger),
        )
        return

    async with aiohttp.request(
        "GET",
        "https://www.googleapis.com/youtube/v3/search?",
        params={
            "part": "snippet",
            "maxResults": results_count,
            "q": search_words[-1],
            "key": bot.config.yt_api_key,
        },
    ) as resp:
        search_results = await resp.json()
        results = []
        for item in search_results["items"]:
            if item["id"]["kind"] == "youtube#video":
                item_id = item["id"]["videoId"]
                item_url = "https://youtu.be/" + item_id
            elif item["id"]["kind"] == "youtube#playlist":
                item_id = item["id"]["playlistId"]
                item_url = "https://www.youtube.com/playlist?list=" + item_id
            else:
                continue
            results.append(
                "%s (by %s) %s"
                % (item["snippet"]["title"], item["snippet"]["channelTitle"], item_url)
            )
        bot.send_many(target=msg.channel, messages=results)
