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
import moviepy.editor as mp
from pydub import AudioSegment
from yt_dlp import YoutubeDL, utils

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
search_api = "https://play.radiojavan.com/api/p/search?query="
artist_api = "https://play.radiojavan.com/api/p/artist?v=2&query="
video_api = "https://play.radiojavan.com/api/p/video?id="
album_api = "https://play.radiojavan.com/api/p/mp3?album=1&id="


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


async def download_with_ydl(url, update, context):
    with YoutubeDL(ydl_opts) as ydl:
        # download
        # ydl.download([url])
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Getting information of the link ... 👨🏻‍💻")
        info_dict = ydl.extract_info(url, download=False)

        is_playlist = info_dict.get("_type") == "playlist"
        if is_playlist:
            downloadin_text = f"Downloading {info_dict.get('title')} ({len(info_dict.get('entries'))} items) ... 😇"
        else:
            downloadin_text = f"Downloading {info_dict.get('title')} ... 😇"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=downloadin_text)

        try:
            ydl.download([url])

            if is_playlist:
                for item in info_dict.get('entries'):
                    buttons = [InlineKeyboardButton("👍", callback_data="like"),
                               InlineKeyboardButton("👎", callback_data="dislike")]

                    reply_markup = InlineKeyboardMarkup(
                        build_menu(buttons, n_cols=2))

                    filename = "mp3s/" + item.get("title") + ".mp3"
                    thumbnail_filename = "thumbnails/" + \
                        item.get("title") + ".jpg"
                    thumbnail_url = item.get("thumbnail")
                    download(thumbnail_url, thumbnail_filename)
                    if os.path.exists(filename) and os.path.exists(thumbnail_filename):
                        with open(filename, "rb") as f:
                            thumbnail_file = open(thumbnail_filename, "rb")
                            text = "Here is your mp3 😌🎧"
                            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=thumbnail_file)
                            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=text, performer=item.get("uploader"), title=item.get("title"), thumbnail=thumbnail_file, reply_markup=reply_markup)
            else:
                buttons = [InlineKeyboardButton("👍", callback_data="like"),
                           InlineKeyboardButton("👎", callback_data="dislike")]

                reply_markup = InlineKeyboardMarkup(
                    build_menu(buttons, n_cols=2))

                filename = "mp3s/" + info_dict.get("title") + ".mp3"
                thumbnail_filename = "thumbnails/" + \
                    info_dict.get("title") + ".jpg"
                thumbnail_url = info_dict.get("thumbnail")
                download(thumbnail_url, thumbnail_filename)
                with open(filename, "rb") as f:
                    thumbnail_file = open(thumbnail_filename, "rb")
                    text = "Here is your mp3 😌🎧"
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=thumbnail_file)
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=text, performer=info_dict.get("uploader"), title=info_dict.get("title"), thumbnail=thumbnail_file, reply_markup=reply_markup)
        except utils.DownloadError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Unfortunately the link is not downloadable ... 😢")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton("/playlists Top Playlists 😎")]]
    # buttons = [[MenuButton("commands")]]
    reply_markup = ReplyKeyboardMarkup(buttons)
    name = update.message.from_user.first_name
    chat_buttons = await context.bot.get_chat_menu_button(chat_id=update.effective_chat.id)
    logger.info(chat_buttons)
    # await context.bot.set_chat_menu_button(chat_id=update.effective_chat.id, menu_button=MenuButton("commands"))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello "+name+".\nI'm a bot created by @fxckedupabcde for downloading musics! start searching your music by sending me the artist name or the song name or the album name. You can also use command /playlists to get the Top playlists. Send /help if you want help.", reply_markup=reply_markup)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """Here is the list of things you can do with this bot.
1- You can search any song, album, artist or playlist by sending a part of the title or full title of them, for example if I want to listen to Irane Man performed by Sogand, There's multiple ways to achieve that song.
A) send `irane man` to bot and select the `mp3s` then download the song.
B) send `sogand` to bot and select `artists` or `mp3s` then download the song.
Also you can explose every artists mp3s, albums, and music videos by searching their name.
2- You can use command /playlists to get the top playlists on RadioJavan, and download their songs.
3- You can use command /youtube to download mp3 of a video on youtube. You should pass the link of the video after command, like this: /youtube https://www.youtube.com/watch?v=cDNDVtoJhik&ab_channel=MohsenYeganeh
This command also support youtube playlists. It will download all of the tracks of the playlist.
4- You can use command /soundcloud to download songs on the soundcloud. You should pass the link of the song, like this: /soundcloud https://soundcloud.com/mrkitty_sc/after-dark
This command also supports soundcloud sets (playlists). It will download all of the tracks of the set.

Bot will be updated as usual as possible, and you can share your ideas and opininons with me. Feel free to contact with me @fxckedupabcde 👨🏻‍💻
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

@send_typing_action
async def playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(home_items, headers=headers)
    if response.status_code == 200:
        json_data = response.json()

        for section in json_data["sections"]:
            if "id" in section and section["id"] == "playlists":
                items = section["items"]
                for idx, item in enumerate(items):
                    button_list = [InlineKeyboardButton(
                        f"{playlist['title']} ({playlist['items_count']} songs)", callback_data=f"playlist;{playlist['id']}") for playlist in items]
                reply_markup = InlineKeyboardMarkup(
                    build_menu(button_list, n_cols=1))
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Top playlists ...", reply_markup=reply_markup)
    # ch = int(input("Choose one playlist: "))

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'mp3s/%(title)s.%(ext)s',
    # 'writethumbnail': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}


@send_typing_action
async def youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yt_url = context.args[0]

    await download_with_ydl(yt_url, update, context)


@send_typing_action
async def soundcloud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sc_url = context.args[0]

    await download_with_ydl(sc_url, update, context)


async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    print(f"[INFO] {query=}")

    chat_user = update.effective_user
    chat = update.effective_chat

    input_text = query.data
    input_text_parts = input_text.split(";")

    command = input_text_parts[0]

    if command == "search":
        search_query = input_text_parts[1]

        if search_query == "_direct_":
            artist_query = input_text_parts[2]
            search_key = input_text_parts[3]
            search_res = requests.get(
                artist_api + artist_query, headers=headers
            ).json()[search_key]
        else:
            search_key = input_text_parts[2]
            search_res = requests.get(
                search_api + search_query, headers=headers).json()[search_key]

        if search_key == 'artists':
            for item in search_res:
                button_list = [InlineKeyboardButton(
                    f"{item['name']} ({item['type']})", callback_data=f"{item['type']};{item['query']}")]
                reply_markup = InlineKeyboardMarkup(
                    build_menu(button_list, n_cols=1))
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=item["photo"], reply_markup=reply_markup)
            # await query.edit_message_reply_markup(reply_markup=reply_markup)

        if search_key == 'videos' or search_key == 'mp3s':
            button_list = [InlineKeyboardButton(
                f"{item['title']} ({item['type']})", callback_data=f"{item['type']};{item['id']}") for item in search_res]
            reply_markup = InlineKeyboardMarkup(
                build_menu(button_list, n_cols=1))
            await query.edit_message_reply_markup(reply_markup=reply_markup)

        if search_key == 'albums':
            for item in search_res:
                button_list = [InlineKeyboardButton(f"{item['album']['artist']} - {item['album']['album']} (album)",
                                                    callback_data=f"album;{item['album']['id']}")]
                reply_markup = InlineKeyboardMarkup(
                    build_menu(button_list, n_cols=1))
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=item["photo"], reply_markup=reply_markup)

        if search_key == 'playlists':
            for item in search_res:
                button_list = [InlineKeyboardButton(f"{item['playlist']['title']} ({item['playlist']['type']} - {item['playlist']['created_by']})",
                                                    callback_data=f"{item['type']};{item['playlist']['id']}")]
                reply_markup = InlineKeyboardMarkup(
                    build_menu(button_list, n_cols=1))
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=item['playlist']["photo"], reply_markup=reply_markup)

    if command == "artist":
        artist_query = input_text_parts[1]
        artist_items = requests.get(
            artist_api + artist_query, headers=headers
        ).json()

        needed_keys = ["albums", "mp3s", "videos", "podcasts", "playlists"]
        button_list = []
        for key in needed_keys:
            if len(artist_items[key]) > 0:
                button_list.append(InlineKeyboardButton(
                    f"{key} ({len(artist_items[key])} items)", callback_data=f"search;_direct_;{artist_query};{key}"))
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    if command == "video":
        video_id = input_text_parts[1]
        video_item = requests.get(
            video_api + video_id, headers=headers
        ).json()

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Downloading video on the server ... 👨🏻‍💻")
        url = video_item["link"]
        filename = "videos/" + video_item["permlink"] + ".mp4"
        thumbnail_filename = "thumbnails/" + video_item["permlink"] + ".jpg"
        thumbnail_url = video_item["photo"]
        download(url, filename)
        download(thumbnail_url, thumbnail_filename)

        text = """Compressing video ... 👨🏻‍💻😮‍💨
This may take a long time, be patient 😇"""
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        filename_lq = "videos/" + video_item["permlink"] + "_lq.mp4"

        # Load the video file
        video = mp.VideoFileClip(filename)

        # Define the target file size (in bytes)
        # target_size = 50 * 1024 * 1024

        # Calculate the current bitrate of the video
        # current_bitrate = video.bitrate

        # Calculate the new bitrate required to achieve the target size
        # new_bitrate = current_bitrate * target_size / video.size

        duration = video.duration

        # lower size
        if not os.path.exists(filename_lq):
            # Set the new bitrate and resize the video
            processed_video = video.resize(height=360)

            # Write the processed video to a new file
            processed_video.write_videofile(filename_lq, codec="libx264")

        with open(filename_lq, "rb") as f:
            thumbnail_file = open(thumbnail_filename, "rb")
            text = f"Finally your video is here: {video_item['song']} (by {video_item['artist']}) 😍"
            # emotion buttons
            buttons = [InlineKeyboardButton("👍", callback_data="like"),
                       InlineKeyboardButton("👎", callback_data="dislike")]

            reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
            # await query.edit_message_reply_markup(None)
            await context.bot.send_video(chat_id=update.effective_chat.id, video=f, duration=duration, thumbnail=thumbnail_file, caption=text, reply_markup=reply_markup, supports_streaming=True)

    if command == "album":
        album_id = input_text_parts[1]
        album_items = requests.get(
            album_api + album_id, headers=headers
        ).json()

        button_list = [InlineKeyboardButton(
            f"{song['song']} (by {song['artist']})", callback_data=f"mp3;{song['id']}") for song in album_items["album_tracks"]]
        reply_markup = InlineKeyboardMarkup(
            build_menu(button_list, n_cols=1))

        await query.edit_message_reply_markup(reply_markup=reply_markup)

    if command == "playlist":
        playlist_id = input_text_parts[1]
        mp3s_list = requests.get(
            playlist_items + playlist_id, headers=headers
        ).json()

        playlist_songs = mp3s_list["items"]
        # print(playlist_songs)
        button_list = [InlineKeyboardButton(
            f"{song['song']} (by {song['artist']})", callback_data=f"mp3;{song['id']}") for song in playlist_songs]
        reply_markup = InlineKeyboardMarkup(
            build_menu(button_list, n_cols=1))

        await query.edit_message_reply_markup(reply_markup=reply_markup)

    if command == "mp3":
        song_id = input_text_parts[1]
        # print(song_id)
        mp3_item = requests.get(
            mp3_api + song_id, headers=headers
        ).json()

        url = mp3_item["link"]
        filename = "mp3s/" + mp3_item["permlink"] + ".mp3"
        thumbnail_filename = "thumbnails/" + mp3_item["permlink"] + ".jpg"
        thumbnail_url = mp3_item["photo"]
        download(url, filename)
        download(thumbnail_url, thumbnail_filename)

        # Load the MP3 file
        audio = AudioSegment.from_file(filename, format="mp3")

        # Get the length of the audio file in milliseconds
        length = len(audio)

        # Set the start and end points for trimming
        start = length / 2 - 10000  # starting 10 seconds before the midpoint
        end = length / 2 + 10000   # ending 10 seconds after the midpoint

        # Trim the audio file
        trimmed_audio = audio[start:end]

        # Export the trimmed audio file as an MP3
        trimmed_filename = "mp3s/" + mp3_item["permlink"] + "_tr.ogg"
        trimmed_audio.export(trimmed_filename, format="ogg")

        with open(filename, "rb") as f:
            thumbnail_file = open(thumbnail_filename, "rb")
            trimmed_file = open(trimmed_filename, "rb")
            text = f"{mp3_item['song']} (by {mp3_item['artist']})"
            # emotion buttons
            buttons = [InlineKeyboardButton("👍", callback_data="like"),
                       InlineKeyboardButton("👎", callback_data="dislike")]

            reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=mp3_item["photo"])
            # await query.edit_message_reply_markup(None)
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=trimmed_file, duration=20)
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=text, performer=mp3_item['artist'], title=mp3_item['song'], thumbnail=thumbnail_file, reply_markup=reply_markup)

    await query.answer()


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    print(f"[INFO] search {query=}")
    search_res = requests.get(search_api + query, headers=headers).json()
    button_list = []
    not_needed_keys = ["top", "all_artists",
                       "profiles", "query", "shows", "lyrics"]
    for key in search_res:
        if key not in not_needed_keys and len(search_res[key]) > 0:
            button_list.append(InlineKeyboardButton(
                f"{key} ({len(search_res[key])} items)", callback_data=f"search;{query};{key}"))
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="results ...", reply_markup=reply_markup)
    # if key == "artists":
    #     button_list = [InlineKeyboardButton(
    #             f"{artist['name']} (artist)", callback_data=f"artist;{artist['id']}") for artist in search_res[key]]
    #     reply_markup = InlineKeyboardMarkup(
    #                 build_menu(button_list, n_cols=1))
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text="results ...", reply_markup=reply_markup)
    # elif key == "mp3s":
    #     button_list = [InlineKeyboardButton(
    #             f"{mp3['title']} (song)", callback_data=f"mp3;{mp3['id']}") for mp3 in search_res[key]]
    #     reply_markup = InlineKeyboardMarkup(
    #                 build_menu(button_list, n_cols=1))
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text="results ...", reply_markup=reply_markup)
    # elif key == "albums":
    #     button_list = [InlineKeyboardButton(
    #             f"{album['title']} (album)", callback_data=f"album;{album['id']}") for album in search_res[key]]
    #     reply_markup = InlineKeyboardMarkup(
    #                 build_menu(button_list, n_cols=1))
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text="results ...", reply_markup=reply_markup)
    # for artist in search_res[key]:

    # await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

if __name__ == '__main__':
    # run bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    search_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), search)

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    playlists_handler = CommandHandler('playlists', playlists)
    youtube_handler = CommandHandler('youtube', youtube)
    soundcloud_handler = CommandHandler('soundcloud', soundcloud)

    application.add_handler(search_handler)
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(playlists_handler)
    application.add_handler(youtube_handler)
    application.add_handler(soundcloud_handler)

    application.add_handler(CallbackQueryHandler(handle_query))

    # application.add_handler(message_handler)

    application.run_polling()
