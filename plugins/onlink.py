import os, asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from plugins.authers import is_authorized
from plugins.tgup import upload_file
from Func.downloader import dl
from Func.utils import mention_user, generate_thumbnail, get_tg_filename
from log import logger as lg
  

@Client.on_message(filters.regex(r'https?://[^\s]+'))
async def handle_link(client, message):
  link = message.text
  if "|" in link:
    link, newName = link.split("|")
  else:
    newName = None
    
  if not is_authorized(message.chat.id):
      await message.reply("**❌️You are not my auther for use me!...❌️**")
      return
  stT = f"🛠**Processing...**"
  msg = await message.reply(stT)
  dl_file = await dl(url=link, msg=msg, custom_filename=newName)
  if dl_file and not "error" in dl_file:
    res = await upload_file(client, message.chat.id, dl_file["file_path"], msg, as_document=False, thumb=None) #try upload
    if res:
      lg.info(f"Uploaded {dl_file['filename']}")
    else:
      lg.info(f"Err on Uploading...")
  else:
    lg.info(f"Err on dl...{dl_file['error']}")
  
  
