import os

from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

from modules.progress import create_progress_bar


TG_MAX_FILESIZE = 50 * 1024 * 1024  # 50 MB
last_error = None


def download_video(url: str, bot, chat_id: int, message_id: int,
                   start_time=None, end_time=None) -> str:
    """Download a video. If start_time/end_time (seconds) are given,
    only that section is downloaded."""
    global last_error
    # Try best quality first, then fall back to lower qualities if file too large
    format_candidates = [
        "bestvideo+bestaudio/best",
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "worst",
    ]

    for fmt in format_candidates:
        options = {
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "format": fmt,
            "noplaylist": True,
            "quiet": False,
            "merge_output_format": "mp4",
            "progress_hooks": [create_progress_bar(bot, chat_id, message_id)],
            # YouTube n-challenge / "page needs to be reloaded" on datacenter IPs
            "remote_components": ["ejs:github"],
        }
        last_error = None

        # Time range cut (e.g. from second 30 to 90)
        if start_time is not None and end_time is not None:
            options["download_ranges"] = download_range_func(
                None, [(start_time, end_time)]
            )
            options["force_keyframes_at_cuts"] = True

        if os.path.exists("cookies.txt"):
            options["cookiefile"] = "cookies.txt"

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            # Check file size before sending
            fsize = os.path.getsize(filename)
            if fsize <= TG_MAX_FILESIZE:
                return filename

            # Too large for Telegram — delete and try next lower format
            os.remove(filename)
            bot.edit_message_text(
                f"⚠️ File too large ({fsize/1024/1024:.1f} MB > 50 MB). "
                f"Trying lower quality…",
                chat_id,
                message_id,
            )

        except Exception as e:
            last_error = str(e)
            print(f"Error with format '{fmt}': {e}")
    # All formats too large or failed — report and let the caller move on
    if last_error:
        bot.send_message(
            chat_id,
            f"❌ Download failed: <code>{last_error[:300]}</code>\n"
            "Try again in a few minutes, or send another link.",
        )
    else:
        bot.send_message(
            chat_id,
            "❌ Even the lowest quality is over Telegram's 50 MB limit.\n"
            "Try a shorter video, or use the time-range feature: <code>link start end</code>",
        )
    return None