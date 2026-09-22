import os, re
import threading
import telebot

from dotenv import load_dotenv

load_dotenv()

from modules.checker import youtube_regex
from modules.downloader import download_video
from modules.spotify_downloader import download_spotify, spotify_link_regex

TOKEN = os.getenv("BOT_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


def setup_cookies():
    cookies_content = os.environ.get("YT_COOKIES")
    if cookies_content:
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(cookies_content)


setup_cookies()


# '/start' command reply
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "Hello, I'm a <b>Simple Youtube Downloader!👋</b>\n\nTo get started, just type the /help command.",
    )


# '/help' command reply
@bot.message_handler(commands=["help"])
def send_help(message):
    bot.reply_to(
        message,
        """
        <b>Just send me your video link.</b> ▶️

<b>⏱️ Download a part of a video:</b>
<i>link start end</i> — seconds or mm:ss:
<code>https://youtu.be/abc 30 90</code>
<code>https://youtu.be/abc 1:30 2:45</code>

<b>🎵 Spotify:</b> send a track/album/playlist link.

<i>Source: <a href="https://github.com/hansanaD/TelegramYTDLBot">TelegramYTDLBot</a> by <a href="https://github.com/DevHanza/">DevHanza</a></i>
        """,
        disable_web_page_preview=True,
    )


TIME_TOKEN = r"\d{1,2}(?::\d{1,2}){0,2}"


def parse_time(t: str):
    """'90' -> 90.0 | '1:30' -> 90.0 | '1:02:03' -> 3723.0"""
    parts = [float(p) for p in t.split(":")]
    seconds = 0.0
    for p in parts:
        seconds = seconds * 60 + p
    return seconds


def handle_youtube(message, url):
    chat_id = message.chat.id
    text = message.text or ""

    # Look for start/end tokens AFTER the URL (pure numbers or mm:ss)
    after_url = text[text.index(url) + len(url):]
    time_tokens = [
        tok for tok in after_url.split()
        if re.fullmatch(TIME_TOKEN, tok)
    ]

    start_time = end_time = None
    if len(time_tokens) == 1:
        bot.reply_to(
            message,
            "⚠️ Give <b>both</b> start and end: <code>link start end</code>",
        )
        return
    elif len(time_tokens) >= 2:
        start_time = parse_time(time_tokens[0])
        end_time = parse_time(time_tokens[1])
        if end_time <= start_time:
            bot.reply_to(message, "⚠️ End must be after start.")
            return
        bot.reply_to(
            message,
            f"⏱️ Downloading from {int(start_time)}s to {int(end_time)}s…",
        )

    status_msg = bot.reply_to(message, "Starting to download..")

    try:
        file_path = download_video(
            url, bot, chat_id, status_msg.message_id,
            start_time=start_time, end_time=end_time,
        )
        if not file_path:
            return  # downloader already reported the error

        with open(file_path, "rb") as file:
            bot.send_video(message.chat.id, file)

        os.remove(file_path)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


def handle_spotify(message, url):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "🎵 Downloading from Spotify…")
    try:
        download_spotify(url, bot, chat_id, status_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


# Link Listener
@bot.message_handler(func=lambda m: True)
def on_message(message):
    # run in background so the bot stays responsive
    threading.Thread(target=route_message, args=(message,)).start()


def route_message(message):
    text = (message.text or "").strip()

    sp = re.search(spotify_link_regex, text)
    if sp:
        handle_spotify(message, sp.group(0))
        return

    m = re.search(youtube_regex, text)
    if m:
        handle_youtube(message, m.group(0))


print("TelegramYTDLBot is running..\n")
bot.delete_webhook(drop_pending_updates=True)
bot.infinity_polling()