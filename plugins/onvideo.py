import os, asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from plugins.authers import is_authorized
from plugins.tgdw import download_file
from plugins.git_up import to_git

download_dir = "/forGit"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

@Client.on_message(filters.command("git"))
async def up_to_git(client, message):
  if not message.reply_to_message or not message.reply_to_message.video:
    await message.reply("Please reply to video message with this command")
    return
  if not is_authorized(message.chat.id):
    await message.reply("**❌️You are not authorized to use me!❌️**")
    return
  v_msg = message.reply_to_message
  v_path=  os.path.join(download_dir,v_msg.video.file_name)
  msg = await message.reply(f"Trying to start!...\n {v_path}")
  file_path = await download_file(client, v_msg, download_dir, msg)
  if file_path:
    r = await to_git(file_path, msg)
    

  
    
