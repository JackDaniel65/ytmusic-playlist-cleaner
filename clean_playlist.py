from ytmusicapi import YTMusic
import time

# ============================================================
# CONFIG
# ============================================================

AUTH_FILE = "browser_clean.json"
PLAYLIST_ID = "PLvvhgOC1L1Rc0XjjZDmR3rLQRJgWXMWMo"

# This is the LAST song we want to keep.
TARGET = "Take Me to the Beach (feat. Ado)"


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    return " ".join(text.lower().strip().split())


# ============================================================
# CONNECT
# ============================================================

print("=" * 70)
print("YOUTUBE MUSIC PLAYLIST CLEANER")
print("=" * 70)

print("\nConnecting to YouTube Music...")

yt = YTMusic(AUTH_FILE)

print("Connected successfully.")


# ============================================================
# GET ENTIRE PLAYLIST
# ============================================================

print("\nFetching ENTIRE playlist...")
print("(This may take a little while for a large playlist.)")

playlist = yt.get_playlist(
    PLAYLIST_ID,
    limit=None
)

tracks = playlist.get("tracks", [])

print(f"\nTotal songs retrieved: {len(tracks)}")


# ============================================================
# FIND TARGET
# ============================================================

target_normalized = normalize(TARGET)

target_index = None

for i, track in enumerate(tracks):
    title = track.get("title", "")

    if normalize(title) == target_normalized:
        target_index = i
        break


# ============================================================
# TARGET NOT FOUND
# ============================================================

if target_index is None:

    print("\n" + "=" * 70)
    print("❌ TARGET SONG NOT FOUND")
    print("=" * 70)

    print(f"\nCould not find:")
    print(f"  {TARGET}")

    print("\nNO CHANGES WERE MADE.")

    raise SystemExit(1)


# ============================================================
# DETERMINE WHAT TO REMOVE
# ============================================================

keep_count = target_index + 1
remove_tracks = tracks[keep_count:]

print("\n" + "=" * 70)
print("TARGET FOUND")
print("=" * 70)

print(f"Last song to KEEP : {tracks[target_index].get('title')}")
print(f"Position          : {keep_count}")
print(f"Total playlist    : {len(tracks)}")
print(f"Songs to REMOVE   : {len(remove_tracks)}")

print("\nSongs after the target will be removed ALL THE WAY")
print("to the actual end of the playlist.")


# ============================================================
# NOTHING TO REMOVE
# ============================================================

if not remove_tracks:

    print("\nNothing needs to be removed.")
    print("Playlist is already ending at the target song.")
    raise SystemExit(0)


# ============================================================
# SHOW BOUNDARIES
# ============================================================

print("\nFirst song that WILL be removed:")
print(f"  {remove_tracks[0].get('title')}")

print("\nLast song that WILL be removed:")
print(f"  {remove_tracks[-1].get('title')}")


# ============================================================
# SAFETY CONFIRMATION
# ============================================================

print("\n" + "=" * 70)
print("⚠️  ABOUT TO MODIFY YOUR PLAYLIST")
print("=" * 70)

print(f"\nKEEPING  : {keep_count} songs")
print(f"REMOVING : {len(remove_tracks)} songs")

confirmation = input(
    "\nType DELETE to permanently remove these songs: "
).strip()

if confirmation != "DELETE":
    print("\nCancelled. NO changes were made.")
    raise SystemExit(0)


# ============================================================
# REMOVE
# ============================================================

print("\nStarting removal...")

# Remove in batches to make the operation safer with a large playlist.
BATCH_SIZE = 50

removed_total = 0

for start in range(0, len(remove_tracks), BATCH_SIZE):

    batch = remove_tracks[start:start + BATCH_SIZE]

    # Only send the fields required by ytmusicapi.
    videos = [
        {
            "videoId": track["videoId"],
            "setVideoId": track["setVideoId"]
        }
        for track in batch
        if track.get("videoId") and track.get("setVideoId")
    ]

    if not videos:
        continue

    batch_number = (start // BATCH_SIZE) + 1
    total_batches = (len(remove_tracks) + BATCH_SIZE - 1) // BATCH_SIZE

    print(
        f"\nRemoving batch {batch_number}/{total_batches} "
        f"({len(videos)} songs)..."
    )

    result = yt.remove_playlist_items(
        PLAYLIST_ID,
        videos
    )

    removed_total += len(videos)

    print(f"Batch completed. Removed so far: {removed_total}")

    # Small pause between batches.
    if start + BATCH_SIZE < len(remove_tracks):
        time.sleep(1)


# ============================================================
# DONE
# ============================================================

print("\n" + "=" * 70)
print("✅ PLAYLIST CLEANUP COMPLETE")
print("=" * 70)

print(f"\nKept songs    : {keep_count}")
print(f"Removed songs : {removed_total}")
print(f"Last kept     : {tracks[target_index].get('title')}")

print("\nThe playlist should now end at:")
print(f"  {TARGET}")

print("\nDone.")
