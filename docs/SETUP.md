# YouTube Music Playlist Cleaner - Setup Guide

## 1. Clone the repository

Use the repository clone command from the GitHub repository.

## 2. Create the virtual environment

Create and activate the Python venv:

``` bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. YouTube Music authentication setup

The program requires your own YouTube Music browser authentication. Every user must configure their own local `browser.json`.

Step-by-step browser process:

1. Open https://music.youtube.com/ and log in.
2. Press ``ctl + shift + `` `I` html manager Developer Tools.
3. Click the ``Network`` tab.
4. In the Network filter box, type `browse`.
5. If available, select Fetch/XHRO to simplify the request list.
6. Keep Developer Tools open and go back to YouTube Music.
7. Open Library > Playlists and open the playlist you want to use.
8. Look for the request with the path ``/youtube/i1/tbrowse?prettyPrint=false``.
9. Select the latest relevant `browse` that was generated while loading the playlist or library.
10-. DO NOT select ``/youtube/i1/att/get?prettyPrint=false``. That is a different request.
11. With the correct `browse` request selected, click ``Headers`` on the right.
12. Scroll to `Request Headers`.
13. Confirm that the headers include the authentication fields required by the example file.
14. Copy the request header data and use it only for your local configuration.

## 4. Create browser.json

From the project directory:

``` bash
cp browser.example.json browser.json
nano browser.json
```

Use `browser.example.json` as the structure reference and configure the file with your own authentication data.

## 5. Security

This authentication data can be sensitive. Do NOT share or upload your real `browser.json` or `browser_clean.json` to GitHb.

These files are intentionally ignored by Git. Verify with:

```bash
git check-ignore -v browser.json
```

## 6. Run the project

```bash
source venv/bin/activate
python3 clean_playlist.py
```

## 7. Features

The program supports:

- Selecting a playlist by number or name.
- Scanning and showing the total song count.
- Deleting a range of positions, for example 125-230.
- Deleting specific positions.
- Finding a song by name.
- Confirming the song name and position before deleting by name.
- Deleting everything between two song names.
- Deleting everything after a selected song.
- Previewing the changes before deletion.
- Requiring explicit confirmation before destructive changes.

## 8. Authentication errors

If authentication stops working or the program returns HTTP 400 / JSON decoding errors, use the same Network process above to obtain fresh local authentication and update only your copy of `browser.json`.

## 9. Short workflow

#** Clone -> venv -> pip install -> browser authentication -> configure beased on example -> run cleaner.

## Security reminder

Never commit or share your local authentication files.
