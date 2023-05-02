from yt_dlp import YoutubeDL, utils
import json


class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


# ℹ️ See "progress_hooks" in help(yt_dlp.YoutubeDL)
def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')


# Set options for downloading audio
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

# Enter video URL
# url = "https://www.youtube.com/watch?v=jda3rOzcXLg&list=PLUppHI532y_tmG7dsburlQvhs-G2eV2N0&ab_channel=potansiyelzampara"
url = "https://soundcloud.com/bahramnouraei/sets/khodha"

# Create YoutubeDL object with options
with YoutubeDL(ydl_opts) as ydl:
    # download
    # ydl.download([url])

    try:
        # extract info without downloading
        info = ydl.extract_info(url, download=False)

        print(json.dumps(ydl.sanitize_info(info)))
    except utils.DownloadError:
        print("Link is not downloadable.")
