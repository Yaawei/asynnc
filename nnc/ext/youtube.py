import aiohttp

from nnc.core.plugin import cmd


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
