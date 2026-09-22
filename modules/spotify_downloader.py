import os
import subprocess

spotify_link_regex = r"https?://open\.spotify\.com/(?:intl-[a-z]{2}/)?(?:track|album|playlist)/[A-Za-z0-9]+"


def download_spotify(url: str, bot, chat_id: int, message_id: int):
    """Download a Spotify track/album/playlist with spotdl and send the files.

    Requires SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET env vars
    (Spotify Developer Dashboard -> Create App).
    Falls back to a clear error message if they are missing.
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not (client_id and client_secret):
        bot.send_message(
            chat_id,
            "⚠️ Spotify support is not configured yet.\n"
            "The bot owner needs to add SPOTIFY_CLIENT_ID and "
            "SPOTIFY_CLIENT_SECRET (from developer.spotify.com).",
        )
        return

    os.makedirs("downloads", exist_ok=True)

    cmd = [
        "spotdl", url,
        "--output", "downloads/{title}-{artists}.mp3",
        "--format", "mp3",
        "--bitrate", "192k",
        "--client-id", client_id,
        "--client-secret", client_secret,
    ]

    bot.edit_message_text("🎵 Fetching metadata and downloading audio…", chat_id, message_id)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    print(result.stdout[-2000:] if result.stdout else "")
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error")[-500:]
        print(f"spotdl failed: {err}")
        bot.edit_message_text(
            f"❌ Spotify download failed:\n<code>{err[:300]}</code>",
            chat_id, message_id,
        )
        return

    files = [
        os.path.join("downloads", f)
        for f in os.listdir("downloads")
        if f.endswith(".mp3")
    ]

    if not files:
        bot.edit_message_text("❌ No audio files were downloaded.", chat_id, message_id)
        return

    bot.edit_message_text(f"📤 Sending {len(files)} file(s)…", chat_id, message_id)

    for f in files:
        size = os.path.getsize(f)
        if size > 50 * 1024 * 1024:
            bot.send_message(chat_id, f"⚠️ {os.path.basename(f)} is over 50 MB — skipped.")
            continue
        with open(f, "rb") as audio:
            bot.send_audio(chat_id, audio)
        os.remove(f)

    bot.edit_message_text("✅ Done!", chat_id, message_id)