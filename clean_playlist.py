#!/usr/bin/env python3

import json
import os
import re
import sys
import time
from pathlib import Path

try:
    from ytmusicapi import YTMusic
except ImportError:
    print("\nERROR: ytmusicapi is not installed.")
    print("Run: pip install -r requirements.txt\n")
    sys.exit(1)


# ============================================================
# CONFIG
# ============================================================

AUTH_FILES = [
    "browser_clean.json",
    "browser.json",
]

DELETE_BATCH_SIZE = 50


# ============================================================
# HELPERS
# ============================================================

def clear_screen():
    os.system("clear")


def normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().casefold())


def get_auth_file():
    for filename in AUTH_FILES:
        path = Path(filename)
        if path.exists():
            return path
    return None


def load_ytmusic():
    auth_file = get_auth_file()

    if auth_file is None:
        print("\nERROR: No authentication file found.")
        print("Expected one of:")
        print("  browser.json")
        print("  browser_clean.json")
        print("\nSee the project setup instructions.")
        sys.exit(1)

    try:
        with open(auth_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Remove debugging artifacts that may have been copied
        # from DevTools.
        junk_keys = {
            "Decoded",
            "/youtubei/v1/browse?prettyPrint=false",
            "/youtubei/v1/att/get?prettyPrint=false",
        }

        headers = {
            k: v for k, v in data.items()
            if k not in junk_keys and isinstance(v, str)
        }

        # These are the important browser-auth headers.
        required = ["cookie", "authorization", "user-agent"]

        missing = [x for x in required if not headers.get(x)]

        if missing:
            print("\nERROR: Authentication file is missing:")
            for item in missing:
                print("  -", item)
            print("\nRecreate browser.json using the setup instructions.")
            sys.exit(1)

        print(f"\nUsing authentication: {auth_file}")

        return YTMusic(headers)

    except json.JSONDecodeError:
        print(f"\nERROR: {auth_file} is not valid JSON.")
        sys.exit(1)
    except Exception as e:
        print("\nERROR while loading YouTube Music authentication:")
        print(type(e).__name__, str(e))
        sys.exit(1)


def pause():
    input("\nPress Enter to continue...")


def print_song(song, position=None):
    title = song.get("title", "Unknown title")
    artists = song.get("artists", [])

    artist_text = ", ".join(
        a.get("name", "") for a in artists if a.get("name")
    )

    if position is not None:
        prefix = f"{position:4}. "
    else:
        prefix = ""

    if artist_text:
        print(f"{prefix}{title} — {artist_text}")
    else:
        print(f"{prefix}{title}")


def fetch_playlist(yt, playlist_id):
    print("\nScanning playlist. Please wait...")

    try:
        result = yt.get_playlist(
            playlist_id,
            limit=None,
            related=False,
            suggestions_limit=0,
        )
        tracks = result.get("tracks", [])

        # Remove unavailable/empty entries only when they have
        # absolutely no useful identifier.
        tracks = [
            t for t in tracks
            if t.get("videoId") or t.get("setVideoId")
        ]

        return result, tracks

    except Exception as e:
        print("\nERROR while reading playlist:")
        print(type(e).__name__, str(e))
        return None, None


# ============================================================
# PLAYLIST SELECTION
# ============================================================

def get_playlists(yt):
    print("\nLoading your YouTube Music playlists...")

    try:
        playlists = yt.get_library_playlists(limit=None)
        return [
            p for p in playlists
            if p.get("playlistId") and p.get("playlistId") != "SE"
        ]
    except Exception as e:
        print("\nERROR while loading playlists:")
        print(type(e).__name__, str(e))
        return []


def select_playlist(yt):
    playlists = get_playlists(yt)

    if not playlists:
        print("\nNo playlists found.")
        pause()
        return None

    while True:
        clear_screen()

        print("=" * 72)
        print("                 YOUR YOUTUBE MUSIC PLAYLISTS")
        print("=" * 72)

        for i, p in enumerate(playlists, 1):
            title = p.get("title", "Untitled")
            count = p.get("count", "?")
            print(f"{i:3}. {title}  [{count} songs]")

        print("\nType a playlist number OR enter its name.")
        print("Type 'q' to quit.")

        choice = input("\nPlaylist: ").strip()

        if choice.lower() == "q":
            return None

        if choice.isdigit():
            number = int(choice)

            if 1 <= number <= len(playlists):
                selected = playlists[number - 1]
                break

            print("\nInvalid playlist number.")
            time.sleep(1)
            continue

        matches = [
            p for p in playlists
            if normalize(choice) in normalize(p.get("title", ""))
        ]

        if len(matches) == 1:
            selected = matches[0]
            break

        if len(matches) > 1:
            print("\nMultiple playlists matched:")
            for i, p in enumerate(matches, 1):
                print(f"{i}. {p.get('title')}")
            pause()
            continue

        print("\nNo playlist matched that name.")
        time.sleep(1)

    return selected


# ============================================================
# CONFIRMATION
# ============================================================

def confirm_delete(songs, description):
    print("\n" + "=" * 72)
    print("                         DELETE PREVIEW")
    print("=" * 72)

    print(f"\n{description}")
    print(f"\nTotal songs to remove: {len(songs)}\n")

    for pos, song in songs:
        print_song(song, pos)

    print("\n" + "-" * 72)
    print("THIS WILL MODIFY YOUR YOUTUBE MUSIC PLAYLIST.")
    print("Type DELETE exactly to continue.")
    print("Anything else cancels.")
    print("-" * 72)

    answer = input("\nConfirmation: ").strip()

    return answer == "DELETE"


def perform_delete(yt, playlist_id, songs):
    if not songs:
        print("\nNothing to delete.")
        return False

    # The API requires playlist item dictionaries containing
    # videoId and setVideoId.
    items = []

    for _, song in songs:
        video_id = song.get("videoId")
        set_video_id = song.get("setVideoId")

        if video_id and set_video_id:
            items.append({
                "videoId": video_id,
                "setVideoId": set_video_id,
            })

    if not items:
        print("\nERROR: No removable playlist items were found.")
        return False

    print(f"\nRemoving {len(items)} songs...")

    try:
        total = len(items)

        for start in range(0, total, DELETE_BATCH_SIZE):
            batch = items[start:start + DELETE_BATCH_SIZE]

            yt.remove_playlist_items(
                playlist_id,
                batch,
            )

            done = min(start + len(batch), total)
            print(f"  Removed {done}/{total}")

            # Small delay helps avoid hammering the endpoint.
            if done < total:
                time.sleep(0.5)

        print("\nSUCCESS: Playlist updated.")
        return True

    except Exception as e:
        print("\nERROR while deleting songs:")
        print(type(e).__name__, str(e))
        print("\nSome earlier batches may already have been removed.")
        return False


# ============================================================
# SONG SEARCH
# ============================================================

def find_song_matches(tracks, query):
    q = normalize(query)

    exact = []
    partial = []

    for pos, song in enumerate(tracks, 1):
        title = normalize(song.get("title", ""))

        if title == q:
            exact.append((pos, song))
        elif q in title:
            partial.append((pos, song))

    if exact:
        return exact

    return partial


def choose_song_match(matches, label="song"):
    if not matches:
        print(f"\nNo {label} found.")
        return None

    if len(matches) == 1:
        return matches[0]

    print(f"\nMultiple {label}s found:\n")

    for i, (pos, song) in enumerate(matches, 1):
        print(f"{i}. Position {pos}")
        print_song(song)
        print()

    while True:
        choice = input("Choose the correct number (or q to cancel): ").strip()

        if choice.lower() == "q":
            return None

        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(matches):
                return matches[n - 1]

        print("Invalid choice.")


# ============================================================
# OPERATIONS
# ============================================================

def delete_range(yt, playlist_id, tracks):
    print("\nDelete songs by position range.")
    print("Example: 125 to 230")

    try:
        start = int(input("\nStart position: ").strip())
        end = int(input("End position: ").strip())
    except ValueError:
        print("\nPositions must be numbers.")
        pause()
        return

    if start > end:
        start, end = end, start

    if start < 1 or end > len(tracks):
        print(f"\nRange must be between 1 and {len(tracks)}.")
        pause()
        return

    selected = [
        (pos, tracks[pos - 1])
        for pos in range(start, end + 1)
    ]

    if confirm_delete(
        selected,
        f"Delete songs {start} through {end} (inclusive)?",
    ):
        perform_delete(yt, playlist_id, selected)
    else:
        print("\nCancelled.")

    pause()


def delete_between_songs(yt, playlist_id, tracks):
    print("\nDelete everything BETWEEN two songs.")
    print("The two boundary songs themselves will be KEPT.")

    first_name = input("\nFirst song name: ").strip()

    if not first_name:
        return

    first_matches = find_song_matches(tracks, first_name)
    first = choose_song_match(first_matches, "first song")

    if not first:
        pause()
        return

    second_name = input("\nSecond song name: ").strip()

    if not second_name:
        return

    second_matches = find_song_matches(tracks, second_name)
    second = choose_song_match(second_matches, "second song")

    if not second:
        pause()
        return

    first_pos, first_song = first
    second_pos, second_song = second

    if first_pos == second_pos:
        print("\nBoth names point to the same song.")
        pause()
        return

    low = min(first_pos, second_pos)
    high = max(first_pos, second_pos)

    if high - low <= 1:
        print("\nThere are no songs between these two songs.")
        pause()
        return

    selected = [
        (pos, tracks[pos - 1])
        for pos in range(low + 1, high)
    ]

    print("\nBoundary songs:")
    print_song(first_song, first_pos)
    print_song(second_song, second_pos)

    if confirm_delete(
        selected,
        f"Delete everything between positions {low} and {high}? "
        f"The boundary songs will remain.",
    ):
        perform_delete(yt, playlist_id, selected)
    else:
        print("\nCancelled.")

    pause()


def delete_specific_positions(yt, playlist_id, tracks):
    print("\nDelete specific positions.")
    print("Example: 12,47,89,125")

    raw = input("\nPositions: ").strip()

    try:
        positions = sorted(set(
            int(x.strip())
            for x in raw.split(",")
            if x.strip()
        ))
    except ValueError:
        print("\nInvalid position list.")
        pause()
        return

    if not positions:
        print("\nNo positions entered.")
        pause()
        return

    invalid = [
        p for p in positions
        if p < 1 or p > len(tracks)
    ]

    if invalid:
        print(f"\nInvalid positions: {invalid}")
        print(f"Valid range: 1-{len(tracks)}")
        pause()
        return

    selected = [
        (pos, tracks[pos - 1])
        for pos in positions
    ]

    if confirm_delete(
        selected,
        "Delete these specific songs?",
    ):
        perform_delete(yt, playlist_id, selected)
    else:
        print("\nCancelled.")

    pause()


def delete_by_name(yt, playlist_id, tracks):
    print("\nDelete one song by name.")

    query = input("\nSong name: ").strip()

    if not query:
        return

    matches = find_song_matches(tracks, query)
    selected = choose_song_match(matches)

    if not selected:
        pause()
        return

    pos, song = selected

    print("\nFOUND SONG:")
    print_song(song, pos)

    if confirm_delete(
        [selected],
        f"Delete the song found at position {pos}?",
    ):
        perform_delete(yt, playlist_id, [selected])
    else:
        print("\nCancelled.")

    pause()


def delete_after_song(yt, playlist_id, tracks):
    print("\nRemove EVERYTHING AFTER a selected song.")
    print("The selected song itself will be KEPT.")

    query = input("\nSong name: ").strip()

    if not query:
        return

    matches = find_song_matches(tracks, query)
    selected = choose_song_match(matches)

    if not selected:
        pause()
        return

    pos, song = selected

    if pos >= len(tracks):
        print("\nThat song is already the last song.")
        pause()
        return

    songs_to_remove = [
        (p, tracks[p - 1])
        for p in range(pos + 1, len(tracks) + 1)
    ]

    print("\nLAST KEPT SONG:")
    print_song(song, pos)

    if confirm_delete(
        songs_to_remove,
        f"Remove every song AFTER position {pos}?",
    ):
        perform_delete(
            yt,
            playlist_id,
            songs_to_remove,
        )
    else:
        print("\nCancelled.")

    pause()


def show_search( tracks):
    query = input("\nSearch song name: ").strip()

    if not query:
        return

    matches = find_song_matches(tracks, query)

    if not matches:
        print("\nNo songs found.")
        pause()
        return

    print(f"\nFound {len(matches)} match(es):\n")

    for pos, song in matches:
        print_song(song, pos)

    pause()


def show_playlist(playlist, tracks):
    clear_screen()

    print("=" * 72)
    print(f"PLAYLIST: {playlist.get('title', 'Untitled')}")
    print(f"TOTAL SONGS: {len(tracks)}")
    print("=" * 72)

    if not tracks:
        print("\nPlaylist is empty.")
        pause()
        return

    # Don't dump thousands of songs automatically.
    print("\nFirst 25 songs:\n")

    for pos, song in enumerate(tracks[:25], 1):
        print_song(song, pos)

    if len(tracks) > 25:
        print(f"\n... and {len(tracks) - 25} more.")

    pause()


# ============================================================
# MAIN MENU
# ============================================================

def playlist_menu(yt, playlist):
    playlist_id = playlist["playlistId"]

    while True:
        result, tracks = fetch_playlist(yt, playlist_id)

        if tracks is None:
            pause()
            return

        clear_screen()

        title = result.get(
            "title",
            playlist.get("title", "Untitled"),
        )

        print("=" * 72)
        print("                 YOUTUBE MUSIC PLAYLIST CLEANER")
        print("=" * 72)
        print(f"\nPlaylist : {title}")
        print(f"Songs    : {len(tracks)}")

        print("\n" + "-" * 72)
        print("1. Delete songs by range")
        print("2. Delete songs between two song names")
        print("3. Delete specific songs by number")
        print("4. Delete song by name")
        print("5. Remove EVERYTHING after a song")
        print("6. Search songs")
        print("7. Show first 25 songs")
        print("8. Refresh playlist")
        print("9. Back to playlist selection")
        print("0. Exit")
        print("-" * 72)

        choice = input("\nChoice: ").strip()

        if choice == "1":
            delete_range(yt, playlist_id, tracks)

        elif choice == "2":
            delete_between_songs(yt, playlist_id, tracks)

        elif choice == "3":
            delete_specific_positions(yt, playlist_id, tracks)

        elif choice == "4":
            delete_by_name(yt, playlist_id, tracks)

        elif choice == "5":
            delete_after_song(yt, playlist_id, tracks)

        elif choice == "6":
            show_search(tracks)

        elif choice == "7":
            show_playlist(playlist, tracks)

        elif choice == "8":
            continue

        elif choice == "9":
            return

        elif choice == "0":
            sys.exit(0)

        else:
            print("\nInvalid choice.")
            time.sleep(1)


def main():
    print("=" * 72)
    print("             YOUTUBE MUSIC PLAYLIST CLEANER")
    print("=" * 72)

    yt = load_ytmusic()

    while True:
        playlist = select_playlist(yt)

        if playlist is None:
            print("\nGoodbye.")
            return

        playlist_menu(yt, playlist)


if __name__ == "__main__":
    main()
