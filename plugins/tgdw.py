import os
import time
import asyncio
from pyrogram.errors import FloodWait
from humanize import naturalsize
from log import logger as lg

# Function to download media with progress updates (from a message containing the file)
async def download_file(client, message, file_path, msg):
    # Check if the message contains a document or media
    if not message.document and not message.video and not message.audio and not message.photo:
        await msg.edit_text("❌ No valid media found in the message.")
        return

    # Get file details
    if message.document:
        file_name = message.document.file_name
        file_size = message.document.file_size
        file_info = message.document
    elif message.video:
        file_name = f"{message.video.file_name or 'video'}"
        file_size = message.video.file_size
        file_info = message.video
    elif message.audio:
        file_name = f"{message.audio.file_name or 'audio'}"
        file_size = message.audio.file_size
        file_info = message.audio
    else:
        file_name = f"{message.photo.file_id}.jpg"
        file_size = 0  # Photo size is handled by Telegram on download
        file_info = message.photo

    # Download progress function
    async def progress_func(current, total):
        nonlocal last_msg, last_t
        percent = (current / total) * 100
        speed = current / (time.time() - start_time) if current else 0
        eta = (total - current) / speed if speed > 0 else 0
        msg_text = f"**Downloading...**\n\n📂 Name: `{file_name}`\n📏 Size: {naturalsize(file_size)}\n📤 Downloaded: {naturalsize(current)}/{naturalsize(total)} ({percent:.2f}%)\n⚡ Speed: {naturalsize(speed)}/s\n⏳ ETA: {int(eta)}s"
        
        if last_t == 0 or time.time() - last_t >= 10:
            if msg_text != last_msg:
                try:
                    await msg.edit_text(msg_text)
                    last_msg = msg_text
                    last_t = time.time()
                except FloodWait as e:
                    await asyncio.sleep(e.value)

    last_msg, last_t = "", 0
    start_time = time.time()

    try:
        # Download the file with progress updates
        await client.download_media(
            message=file_info,
            file_name=file_path,
            progress=progress_func,
            progress_args=(msg,)
        )

        # Final message update
        await msg.edit_text(f"✅ **Download Complete!**\n📂 `{file_name}`\n📏 Size: {naturalsize(file_size)}")
        return file_path

    except Exception as e:
        await msg.edit_text(f"❌ Error while downloading the file: {e}")
        lg.error(f"Error downloading file: {e}")
        return

    finally:
        # Handle cleanup if needed
        try:
            # You can perform any cleanup or additional tasks here if necessary
            pass
        except Exception as e:
            print(f"Error during cleanup: {e}")
            lg.error(f"Error during cleanup: {e}")
