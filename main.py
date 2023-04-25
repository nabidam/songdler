import requests
from pprint import pprint
import os

home_items = "https://play.radiojavan.com/api/p/home_items"
playlist_items = "https://play.radiojavan.com/api/p/mp3_playlist_with_items?id="

proxy = {
    "http": "http://127.0.0.1:2080",
    "https": "http://127.0.0.1:2080",
}

headers = {
    "x-api-key": "40e87948bd4ef75efe61205ac5f468a9fd2b970511acf58c49706ecb984f1d67"
}


def download(url, filename):
    filename_parts = filename.split(".")
    print(f"[INFO] Downloading {filename_parts[0]} ...")
    if not os.path.exists(filename):
        response = requests.get(
            url,
            proxies=proxy,
            headers=headers,
            stream=True,
        )

        if response.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print(f"Download failed with error {response.status_code}")


def download_top_50():
    response = requests.get(home_items, proxies=proxy, headers=headers)
    if response.status_code == 200:
        json_data = response.json()

        for section in json_data["sections"]:
            if "id" in section and section["id"] == "playlists":
                items = section["items"]
                for item in items:
                    if "title" in item and item["title"] == "Today's Top Hits":
                        mp3s_list = requests.get(
                            playlist_items + item["id"], proxies=proxy, headers=headers
                        ).json()

                        for mp3_item in mp3s_list["items"]:
                            filename = "mp3s/" + mp3_item["permlink"] + ".mp3"

                            if not os.path.exists(filename):
                                response = requests.get(
                                    mp3_item["link"],
                                    proxies=proxy,
                                    headers=headers,
                                    stream=True,
                                )

                                if response.status_code == 200:
                                    with open(filename, "wb") as f:
                                        for chunk in response.iter_content(
                                            chunk_size=8192
                                        ):
                                            f.write(chunk)
                                else:
                                    print(
                                        f"Download failed with error {response.status_code}"
                                    )
                            pprint(mp3_item)

        # pprint(json_data)
    else:
        print("Error requesting data")


def download_interactive():
    response = requests.get(home_items, proxies=proxy, headers=headers)
    if response.status_code == 200:
        json_data = response.json()

        for section in json_data["sections"]:
            if "id" in section and section["id"] == "playlists":
                items = section["items"]
                for idx, item in enumerate(items):
                    print(
                        f"{idx + 1} - {item['title']} ({item['items_count']} items)")

                ch = int(input("Choose one playlist: "))

                if ch >= 1 or ch <= len(items):
                    item = items[ch - 1]

                    mp3s_list = requests.get(
                        playlist_items + item["id"], proxies=proxy, headers=headers
                    ).json()

                    for idx, mp3_item in enumerate(mp3s_list["items"]):
                        print(
                            f"{idx + 1} - {mp3_item['song']} by {mp3_item['artist']}")

                    ch = input(
                        "Choose titles to download: [ex: 1 or 1 2 3 or 1-5] ")

                    if "-" in ch:
                        parts = ch.split("-")
                        if len(parts) == 2:
                            requested_ids = list(
                                range(int(parts[0]), int(parts[1]) + 1)
                            )
                            for rid in requested_ids:
                                mp3_item = mp3s_list["items"][rid - 1]
                                filename = "mp3s/" + \
                                    mp3_item["permlink"] + ".mp3"
                                download(mp3_item["link"], filename)

                    elif " " in ch:
                        parts = ch.split(" ")
                        for rid in parts:
                            requested_id = int(rid)
                            if requested_id >= 1 or requested_id <= len(
                                mp3s_list["items"]
                            ):
                                mp3_item = mp3s_list["items"][requested_id - 1]
                                filename = "mp3s/" + \
                                    mp3_item["permlink"] + ".mp3"
                                download(mp3_item["link"], filename)

                    else:
                        rid = int(ch)
                        if rid >= 1 or rid <= len(mp3s_list["items"]):
                            mp3_item = mp3s_list["items"][rid - 1]
                            filename = "mp3s/" + mp3_item["permlink"] + ".mp3"
                            download(mp3_item["link"], filename)
                    # if "title" in item and item["title"] == "Today's Top Hits":
                    #     mp3s_list = requests.get(
                    #         playlist_items + item["id"], proxies=proxy, headers=headers
                    #     ).json()

                    #     for mp3_item in mp3s_list["items"]:
                    #         filename = "mp3s/" + mp3_item["permlink"] + ".mp3"

                    #         if not os.path.exists(filename):
                    #             response = requests.get(
                    #                 mp3_item["link"],
                    #                 proxies=proxy,
                    #                 headers=headers,
                    #                 stream=True,
                    #             )

                    #             if response.status_code == 200:
                    #                 with open(filename, "wb") as f:
                    #                     for chunk in response.iter_content(
                    #                         chunk_size=8192
                    #                     ):
                    #                         f.write(chunk)
                    #             else:
                    #                 print(
                    #                     f"Download failed with error {response.status_code}"
                    #                 )
                    #         pprint(mp3_item)

        # pprint(json_data)
    else:
        print("Error requesting data")


def main():
    while True:
        download_interactive()


if __name__ == "__main__":
    main()
