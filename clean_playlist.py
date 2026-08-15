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
DRY_RUN = "--dry-run" in sys.argv


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
    print(chr(10) + "Press Enter to continue...")
    print("Press C to cancel.")
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                key = sys.stdin.read(1)
                if key in ("c", "C"):
                    print(chr(10) + "Cancelled.")
                    return False
                if key in (chr(10), chr(13)):
                    return True
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (ImportError, termios.error, OSError):
        choice = input()
        return choice.strip().lower() != "c"
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
    print("DRY RUN ACTIVE - NO CHANGES WILL BE MADE." if DRY_RUN else "THIS WILL MODIFY YOUR YOUTUBE MUSIC PLAYLIST.")
    print("Type DELETE to preview the operation." if DRY_RUN else "Type DELETE to continue.")
    print("Anything else cancels.")
    print("-" * 72)

    answer = input("\nConfirmation: ").strip()

    return answer.strip().upper() == "DELETE"


def create_playlist_backup(yt, playlist_id, playlist=None, tracks=None):
    if DRY_RUN:
        return None

    try:
        if playlist is None or tracks is None:
            playlist = yt.get_playlist(
                playlist_id,
                limit=None,
                related=False,
                suggestions_limit=0,
            )
            tracks = playlist.get("tracks", [])

        backup_dir = Path("backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        title = str((playlist or {}).get("title", "playlist"))
        safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("._") or "playlist"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{safe_title}_{timestamp}.json"

        backup = {
            "playlistId": playlist_id,
            "title": title,
            "timestamp": timestamp,
            "tracks": tracks,
        }

        with backup_path.open("w", encoding="utf-8") as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)

        print(f"\nBACKUP CREATED: {backup_path}")
        print(f"Songs backed up: {len(tracks)}")
        return backup_path

    except Exception as e:
        print("\nERROR: Could not create playlist backup.")
        print(type(e).__name__, str(e))
        print("Operation cancelled for safety.")
        return False


def create_manual_backup(yt):
    playlist = select_playlist(yt)
    if playlist is None:
        return

    playlist_id = playlist["playlistId"]
    result, tracks = fetch_playlist(yt, playlist_id)

    if tracks is None:
        pause()
        return

    backup = create_playlist_backup(
        yt,
        playlist_id,
        playlist=result or playlist,
        tracks=tracks,
    )

    if backup is not False and backup is not None:
        print("\nManual backup completed successfully.")

    pause()


def list_backups():
    backup_dir = Path("backups")

    if not backup_dir.exists():
        print("\nNo backups found.")
        pause()
        return []

    files = sorted(
        backup_dir.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    if not files:
        print("\nNo backups found.")
        pause()
        return []

    print("\n" + "=" * 72)
    print("                         PLAYLIST BACKUPS")
    print("=" * 72)

    valid = []

    for index, path in enumerate(files, 1):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            title = data.get("title", "Unknown")
            timestamp = data.get("timestamp", "Unknown")
            tracks = data.get("tracks", [])

            print(f"\n{index}. {title}")
            print(f"   Songs     : {len(tracks)}")
            print(f"   Created   : {timestamp}")
            print(f"   File      : {path.name}")

            valid.append(path)

        except (OSError, json.JSONDecodeError, TypeError):
            print(f"\n{index}. INVALID BACKUP")
            print(f"   File      : {path.name}")

    pause()
    return valid


def preview_backup():
    backup_dir = Path("backups")

    if not backup_dir.exists():
        print("\nNo backups found.")
        pause()
        return

    files = sorted(
        backup_dir.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    valid = []

    for path in files:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and isinstance(data.get("tracks"), list):
                valid.append((path, data))

        except (OSError, json.JSONDecodeError, TypeError):
            continue

    if not valid:
        print("\nNo valid backups found.")
        pause()
        return

    print("\n" + "=" * 72)
    print("                       BACKUP PREVIEW")
    print("=" * 72)

    for index, (path, data) in enumerate(valid, 1):
        print(f"\n{index}. {data.get("title", "Unknown")}")
        print(f"   Songs   : {len(data.get("tracks", []))}")
        print(f"   Created : {data.get("timestamp", "Unknown")}")
        print(f"   File    : {path.name}")

    choice = input("\nSelect backup number (or C to cancel): ").strip()

    if choice.lower() == "c":
        print("\nCancelled.")
        return

    if not choice.isdigit():
        print("\nInvalid selection.")
        pause()
        return

    index = int(choice)

    if index < 1 or index > len(valid):
        print("\nInvalid selection.")
        pause()
        return

    path, data = valid[index - 1]
    tracks = data.get("tracks", [])

    print("\n" + "-" * 72)
    print(f"BACKUP: {data.get("title", "Unknown")}")
    print(f"CREATED: {data.get("timestamp", "Unknown")}")
    print(f"SONGS: {len(tracks)}")
    print("-" * 72)

    for pos, song in enumerate(tracks[:25], 1):
        print_song(song, pos)

    if len(tracks) > 25:
        print(f"\n... and {len(tracks) - 25} more.")

    pause()


def choose_backup():
    backup_dir = Path("backups")

    if not backup_dir.exists():
        print("\nNo valid backups found.")
        pause()
        return None

    files = sorted(
        backup_dir.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    valid = []

    for path in files:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if (
                isinstance(data, dict)
                and isinstance(data.get("playlistId"), str)
                and isinstance(data.get("tracks"), list)
            ):
                valid.append((path, data))

        except (OSError, json.JSONDecodeError, TypeError):
            continue

    if not valid:
        print("\nNo valid backups found.")
        pause()
        return None

    print("\n" + "=" * 72)
    print("                         SELECT BACKUP")
    print("=" * 72)

    for index, (path, data) in enumerate(valid, 1):
        tracks = data.get("tracks", [])

        print(f"\n{index}. {data.get('title', 'Unknown')}")
        print(f"   Songs   : {len(tracks)}")
        print(f"   Created : {data.get('timestamp', 'Unknown')}")
        print(f"   File    : {path.name}")

        if tracks:
            print("   Contains:")

            for song in tracks[:5]:
                print(f"     - {song.get('title', 'Unknown title')}")

            if len(tracks) > 5:
                print(f"     ... and {len(tracks) - 5} more")

    choice = input("\nSelect backup number (or C to cancel): ").strip()

    if choice.lower() == "c":
        print("\nCancelled.")
        return None

    if not choice.isdigit():
        print("\nInvalid selection.")
        pause()
        return None

    index = int(choice)

    if index < 1 or index > len(valid):
        print("\nInvalid selection.")
        pause()
        return None

    return valid[index - 1]


def restore_backup(yt):
    selected = choose_backup()

    if selected is None:
        return False

    backup_path, backup_data = selected

    backup_playlist_id = backup_data.get("playlistId")
    backup_title = backup_data.get("title", "Unknown")
    backup_tracks = backup_data.get("tracks", [])

    if not backup_playlist_id:
        print("\nERROR: Backup has no playlist ID.")
        pause()
        return False

    valid_tracks = [
        song for song in backup_tracks
        if song.get("videoId")
    ]

    if not valid_tracks:
        print("\nERROR: Backup contains no restorable songs.")
        pause()
        return False

    print("\n" + "=" * 72)
    print("                         RESTORE BACKUP")
    print("=" * 72)

    print(f"\nBackup : {backup_title}")
    print(f"Songs  : {len(valid_tracks)}")
    print(f"File   : {backup_path.name}")

    print("\nFetching current playlist...")

    current_playlist, current_tracks = fetch_playlist(
        yt,
        backup_playlist_id,
    )

    if current_tracks is None:
        print("\nERROR: Could not read the current playlist.")
        pause()
        return False

    current_title = (
        current_playlist.get("title", backup_title)
        if current_playlist
        else backup_title
    )

    print("\n" + "-" * 72)
    print("RESTORE SUMMARY")
    print("-" * 72)
    print(f"Playlist        : {current_title}")
    print(f"Current songs   : {len(current_tracks)}")
    print(f"Backup songs    : {len(valid_tracks)}")
    print("-" * 72)

    if DRY_RUN:
        print("\nDRY RUN: Restore operation selected.")
        print("NO CHANGES HAVE BEEN MADE.")
        pause()
        return True

    print("\nTHIS WILL REPLACE THE CURRENT PLAYLIST CONTENTS.")
    print("A safety backup will be created before anything is removed.")
    print("The backup contents shown above will be restored.")
    print("-" * 72)

    answer = input("\nType RESTORE to confirm: ").strip()

    if answer.upper() != "RESTORE":
        print("\nCancelled.")
        pause()
        return False

    safety_backup = create_playlist_backup(
        yt,
        backup_playlist_id,
        playlist=current_playlist,
        tracks=current_tracks,
    )

    if safety_backup is False:
        print("\nRestore cancelled because the safety backup failed.")
        pause()
        return False

    removable_items = []

    for song in current_tracks:
        video_id = song.get("videoId")
        set_video_id = song.get("setVideoId")

        if video_id and set_video_id:
            removable_items.append({
                "videoId": video_id,
                "setVideoId": set_video_id,
            })

    restore_video_ids = [
        song["videoId"]
        for song in valid_tracks
    ]

    try:
        if removable_items:
            print(f"\nRemoving {len(removable_items)} current song(s)...")

            for start in range(
                0,
                len(removable_items),
                DELETE_BATCH_SIZE,
            ):
                batch = removable_items[
                    start:start + DELETE_BATCH_SIZE
                ]

                yt.remove_playlist_items(
                    backup_playlist_id,
                    batch,
                )

                done = min(
                    start + len(batch),
                    len(removable_items),
                )

                print(
                    f"  Removed {done}/{len(removable_items)}"
                )

                if done < len(removable_items):
                    time.sleep(0.5)

        print(f"\nAdding {len(restore_video_ids)} backup song(s)...")

        for start in range(
            0,
            len(restore_video_ids),
            DELETE_BATCH_SIZE,
        ):
            batch = restore_video_ids[
                start:start + DELETE_BATCH_SIZE
            ]

            yt.add_playlist_items(
                backup_playlist_id,
                batch,
            )

            done = min(
                start + len(batch),
                len(restore_video_ids),
            )

            print(
                f"  Added {done}/{len(restore_video_ids)}"
            )

            if done < len(restore_video_ids):
                time.sleep(0.5)

        print("\nSUCCESS: Playlist restored from backup.")
        return True

    except Exception as e:
        print("\nERROR while restoring playlist:")
        print(type(e).__name__, str(e))
        print("\nThe safety backup can be used to recover the previous state.")
        return False


def perform_delete(yt, playlist_id, songs):
    if DRY_RUN:
        print(f"\nDRY RUN: Would remove {len(songs)} song(s).")
        print("NO CHANGES HAVE BEEN MADE.")
        return True

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

    backup = create_playlist_backup(yt, playlist_id)
    if backup is False:
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


def delete_full_playlist(yt, playlist):
    if DRY_RUN:
        print(f"\nDRY RUN: Would delete playlist: {playlist.get('title', 'Untitled')}")
        print("NO CHANGES HAVE BEEN MADE.")
        pause()
        return True

    playlist_id = playlist["playlistId"]
    title = playlist.get("title", "Untitled")

    print("\n" + "=" * 72)
    print("                    DELETE ENTIRE PLAYLIST")
    print("=" * 72)
    print(f"\nPlaylist: {title}")
    print("\nTHIS WILL PERMANENTLY DELETE THE ENTIRE PLAYLIST.")
    print("This cannot be undone.")
    print("-" * 72)

    typed = input("\nType the exact playlist name to confirm: ").strip()

    if typed != title:
        print("\nName did not match. Cancelled.")
        pause()
        return False

    backup = create_playlist_backup(yt, playlist_id)
    if backup is False:
        pause()
        return False

    try:
        yt.delete_playlist(playlist_id)
        print(f"\nSUCCESS: '{title}' has been deleted.")
        pause()
        return True
    except Exception as e:
        print("\nERROR while deleting playlist:")
        print(type(e).__name__, str(e))
        pause()
        return False


def merge_playlists(yt, playlist_id, tracks):
    if DRY_RUN:
        print("\nDRY RUN: Merge operation selected.")
        print("NO CHANGES HAVE BEEN MADE.")
        pause()
        return

    print("\n" + "=" * 72)
    print("                       MERGE PLAYLISTS")
    print("=" * 72)
    print("\nSelect the SOURCE playlist to merge INTO the current one.")
    pause()

    source = select_playlist(yt)

    if source is None:
        return

    source_id = source["playlistId"]

    if source_id == playlist_id:
        print("\nCannot merge a playlist into itself.")
        pause()
        return

    print(f"\nFetching songs from '{source.get('title', 'Untitled')}'...")
    _, source_tracks = fetch_playlist(yt, source_id)

    if not source_tracks:
        print("\nSource playlist has no songs (or failed to load).")
        pause()
        return

    existing_ids = {t.get("videoId") for t in tracks if t.get("videoId")}

    video_ids = [
        t["videoId"] for t in source_tracks
        if t.get("videoId") and t["videoId"] not in existing_ids
    ]

    skipped = len(source_tracks) - len(video_ids)

    print(f"\n{len(video_ids)} song(s) will be added.")
    if skipped:
        print(f"{skipped} song(s) skipped (already in target playlist).")

    if not video_ids:
        print("\nNothing to merge.")
        pause()
        return

    answer = input("\nType MERGE to confirm: ").strip()

    if answer.strip().upper() != "MERGE":
        print("\nCancelled.")
        pause()
        return

    backup = create_playlist_backup(yt, playlist_id, tracks=tracks)
    if backup is False:
        pause()
        return

    try:
        for start in range(0, len(video_ids), DELETE_BATCH_SIZE):
            batch = video_ids[start:start + DELETE_BATCH_SIZE]
            yt.add_playlist_items(playlist_id, batch)
            done = min(start + len(batch), len(video_ids))
            print(f"  Added {done}/{len(video_ids)}")
            if done < len(video_ids):
                time.sleep(0.5)

        print("\nSUCCESS: Playlists merged.")
    except Exception as e:
        print("\nERROR while merging playlists:")
        print(type(e).__name__, str(e))

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

def print_main_menu():
    print("\n" + "=" * 72)
    print("                 YOUTUBE MUSIC PLAYLIST CLEANER")
    print("=" * 72)

    if DRY_RUN:
        print("\n              *** DRY RUN MODE ***")
        print("              NO CHANGES WILL BE MADE")
    else:
        print("\n              LIVE MODE")
        print("              Playlist changes are enabled")

    print("\n" + "-" * 72)
    print("PLAYLIST OPERATIONS")
    print("-" * 72)
    print("1. Delete songs by range")
    print("2. Delete songs between two song names")
    print("3. Delete specific songs by number")
    print("4. Delete song by name")
    print("5. Remove EVERYTHING after a song")
    print("8. Merge two playlists")
    print("9. Delete ENTIRE playlist")

    print("\n" + "-" * 72)
    print("BROWSE")
    print("-" * 72)
    print("6. Search songs")
    print("7. Show first 25 songs")

    print("\n" + "-" * 72)
    print("BACKUP & RESTORE")
    print("-" * 72)
    print("10. List backups")
    print("11. Preview backup")
    print("12. Create manual backup")
    print("13. Restore backup")

    print("\n" + "-" * 72)
    print("0. Exit")
    print("-" * 72)

def run_with_playlist(yt, task):
    playlist = select_playlist(yt)

    if playlist is None:
        return

    playlist_id = playlist["playlistId"]

    result, tracks = fetch_playlist(yt, playlist_id)

    if tracks is None:
        pause()
        return

    clear_screen()
    title = result.get("title", playlist.get("title", "Untitled"))
    print("=" * 72)
    print(f"Playlist : {title}")
    print(f"Songs    : {len(tracks)}")
    print("=" * 72)

    if task == "1":
        delete_range(yt, playlist_id, tracks)
    elif task == "2":
        delete_between_songs(yt, playlist_id, tracks)
    elif task == "3":
        delete_specific_positions(yt, playlist_id, tracks)
    elif task == "4":
        delete_by_name(yt, playlist_id, tracks)
    elif task == "5":
        delete_after_song(yt, playlist_id, tracks)
    elif task == "6":
        show_search(tracks)
    elif task == "7":
        show_playlist(playlist, tracks)
    elif task == "8":
        merge_playlists(yt, playlist_id, tracks)


def run_delete_full_playlist(yt):
    playlist = select_playlist(yt)

    if playlist is None:
        return

    delete_full_playlist(yt, playlist)


def main():
    yt = load_ytmusic()

    while True:
        clear_screen()
        print_main_menu()

        choice = input("\nChoice: ").strip()

        if choice in {"1", "2", "3", "4", "5", "6", "7", "8"}:
            run_with_playlist(yt, choice)
        elif choice == "9":
            run_delete_full_playlist(yt)
        elif choice == "10":
            list_backups()
        elif choice == "11":
            preview_backup()
        elif choice == "12":
            create_manual_backup(yt)
        elif choice == "13":
            restore_backup(yt)
        elif choice == "0":
            print("\nGoodbye.")
            sys.exit(0)
        else:
            print("\nInvalid choice.")
            time.sleep(1)


if __name__ == "__main__":
    main()
