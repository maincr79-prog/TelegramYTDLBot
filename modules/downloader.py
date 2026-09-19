import os
from yt_dlp import YoutubeDL

from modules.progress import create_progress_bar


TG_MAX_FILESIZE = 50 * 1024 * 1024  # 50 MB


def download_video(url: str, bot, chat_id: int, message_id: int) -> str:
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
            print(f"Error with format '{fmt}': {e}")

    # All formats too large or failed
    bot.send_message(
        chat_id,
        "❌ Could not download a version under 50 MB (Telegram limit).\n"
        "Try a shorter video or lower quality manually.",
    )
    raise RuntimeError("All download attempts exceeded Telegram 50 MB limit")