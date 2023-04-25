from functools import wraps
import os
import logging
from datetime import datetime
from telegram import Update, constants, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, MenuButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import time
import random
from typing import Union, List
import requests

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
USE_PROXY = "true" in os.getenv('USE_PROXY').lower()
PROXY = os.getenv('PROXY')
CHANNEL_ID = os.getenv('CHANNEL_ID')
RUN_JOB = "true" in os.getenv('RUN_JOB').lower()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return await func(update, context,  *args, **kwargs)
        return command_func

    return decorator


send_typing_action = send_action(constants.ChatAction.TYPING)
send_upload_video_action = send_action(
    constants.ChatAction.UPLOAD_VIDEO)
send_upload_photo_action = send_action(
    constants.ChatAction.UPLOAD_PHOTO)


def build_menu(
    buttons: List[InlineKeyboardButton],
    n_cols: int,
    header_buttons: Union[InlineKeyboardButton,
                          List[InlineKeyboardButton]] = None,
    footer_buttons: Union[InlineKeyboardButton,
                          List[InlineKeyboardButton]] = None
) -> List[List[InlineKeyboardButton]]:
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons if isinstance(
            header_buttons, list) else [header_buttons])
    if footer_buttons:
        menu.append(footer_buttons if isinstance(
            footer_buttons, list) else [footer_buttons])
    return menu


proxy = {
    "http": "http://127.0.0.1:2080",
    "https": "http://127.0.0.1:2080",
}

headers = {
    "x-api-key": "40e87948bd4ef75efe61205ac5f468a9fd2b970511acf58c49706ecb984f1d67"
}

home_items = "https://play.radiojavan.com/api/p/home_items"
playlist_items = "https://play.radiojavan.com/api/p/mp3_playlist_with_items?id="
mp3_api = "https://play.radiojavan.com/api/p/mp3?id="

def download(url, filename):
    filename_parts = filename.split(".")
    print(f"[INFO] Downloading {filename_parts[0]} ...")
    if not os.path.exists(filename):
        response = requests.get(
            url,
            headers=headers,
            stream=True,
        )

        if response.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print(f"Download failed with error {response.status_code}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton("Trends 😎")]]
    # buttons = [[MenuButton("commands")]]
    reply_markup = ReplyKeyboardMarkup(buttons)
    name = update.message.from_user.first_name
    chat_buttons = await context.bot.get_chat_menu_button(chat_id=update.effective_chat.id)
    logger.info(chat_buttons)
    # await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButton("commands"))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello "+name+".\nI'm a bot created by @NabidaM for downloading musics!", reply_markup=reply_markup)


@send_typing_action
async def playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(home_items, headers=headers)
    if response.status_code == 200:
        json_data = response.json()

        for section in json_data["sections"]:
            if "id" in section and section["id"] == "playlists":
                items = section["items"]
                for idx, item in enumerate(items):
                    print(
                        f"{idx + 1} - {item['title']} ({item['items_count']} items)")
                button_list = [InlineKeyboardButton(
                    f"{playlist['title']} ({playlist['items_count']} songs)", callback_data=f"playlist;{playlist['id']}") for playlist in items]
                reply_markup = InlineKeyboardMarkup(
                    build_menu(button_list, n_cols=1))
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Top playlists ...", reply_markup=reply_markup)
    # ch = int(input("Choose one playlist: "))


async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    chat_user = update.effective_user
    chat = update.effective_chat

    input_text = query.data
    input_text_parts = input_text.split(";")

    command = input_text_parts[0]
    if command == "playlist":
        playlist_id = input_text_parts[1]
        mp3s_list = requests.get(
            playlist_items + playlist_id, headers=headers
        ).json()

        playlist_songs = mp3s_list["items"]
        print(playlist_songs)
        button_list = [InlineKeyboardButton(
                    f"{song['song']} (by {song['artist']})", callback_data=f"song;{song['id']}") for song in playlist_songs]
        reply_markup = InlineKeyboardMarkup(
                    build_menu(button_list, n_cols=1))

        await query.edit_message_text(text="Choose your song ...", reply_markup=reply_markup)

    if command == "song":
        song_id = input_text_parts[1]
        print(song_id)
        mp3_item = requests.get(
            mp3_api + song_id, headers=headers
        ).json()

        url = mp3_item["link"]
        filename = "mp3s/" + mp3_item["permlink"] + ".mp3"
        thumbnail_filename = "thumbnails/" + mp3_item["permlink"] + ".jpg"
        thumbnail_url = mp3_item["photo"]
        download(url, filename)
        download(thumbnail_url, thumbnail_filename)

        with open(filename, "rb") as f:
            thumbnail_file = open(thumbnail_filename, "rb")
            text =  f"{mp3_item['song']} (by {mp3_item['artist']})"
            # emotion buttons
            buttons = [InlineKeyboardButton("👍", callback_data="like"),
                    InlineKeyboardButton("👎", callback_data="dislike")]

            reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
            await query.edit_message_text(text=f"Enjoy listening to {text}")
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=text, performer=mp3_item['artist'], title=mp3_item['song'], thumbnail=thumbnail_file, reply_markup=reply_markup)
        
        await query.answer()
        


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a help message"""
    await update.message.reply_text("Use /trends to test this bot.")

if __name__ == '__main__':
    # run bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    playlists_handler = CommandHandler('playlists', playlists)

    application.add_handler(start_handler)
    application.add_handler(playlists_handler)

    application.add_handler(CallbackQueryHandler(handle_query))

    # application.add_handler(message_handler)

    application.run_polling()
