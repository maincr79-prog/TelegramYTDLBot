import os
from yt_dlp import YoutubeDL

from modules.progress import create_progress_bar


def download_video(url: str, bot, chat_id: int, message_id: int) -> str:
    options = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
        "quiet": False,
        "merge_output_format": "mp4",
        "progress_hooks": [create_progress_bar(bot, chat_id, message_id)],
        # YouTube serves JS challenges (n-challenge / "page needs to be
        # reloaded") especially on datacenter IPs like Railway's.
        # yt-dlp needs permission to fetch the EJS solver scripts, and a
        # JS runtime (Deno, installed in the Dockerfile) to run them.
        "remote_components": ["ejs:github"],
    }

    if os.path.exists("cookies.txt"):
        options["cookiefile"] = "cookies.txt"

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return filename

    except Exception as e:
        print(f"Error downloading video: {e} ❌")
        bot.send_message(
            chat_id,
            f"❌ Download failed: <code>{str(e)[:300]}</code>\n"
            "Try again in a few minutes, or send another link.",
            parse_mode="HTML",
        )
        raise
