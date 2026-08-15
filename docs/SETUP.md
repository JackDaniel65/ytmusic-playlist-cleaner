# YouTube Music Playlist Cleaner - Setup Guide

## 1. Clone the repository

git clone https://github.com/JackDaniel65/ytmusic-playlist-cleaner.git
cd ytmusic-playlist-cleaner

## 2. Create the virtual environment

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## 3. Authentication

The application looks for these local authentication files:

1. browser_clean.json
2. browser.json

Do not share these files.

## 4. Test authentication safely

Run the application in dry-run mode first:

python3 clean_playlist.py --dry-run

Dry-run mode allows playlists and songs to be inspected without modifying YouTube Music.

## 5. Live mode

When you are ready to make real playlist changes:

python3 clean_playlist.py

Live mode can modify your YouTube Music playlists.

## 6. Playlist operations

1. Delete songs by range
2. Delete songs between two song names
3. Delete specific songs by number
4. Delete song by name
5. Remove EVERYTHING after a song
8. Merge two playlists
9. Delete ENTIRE playlist

## 7. Browse

6. Search songs
7. Show first 25 songs

## 8. Backup and restore

10. List backups
11. Preview backup
12. Create manual backup
13. Restore backup

Backups are stored locally in:

backups/

Destructive operations create a safety backup before making the API mutation.

If a required safety backup cannot be created, the operation is cancelled.

## 9. Manual backup

Select:

12. Create manual backup

This creates an explicit backup of the selected playlist before making changes.

## 10. Backup listing and preview

Use:

10. List backups

to see available backups, including playlist name, song count, creation time, filename, and backup contents.

Use:

11. Preview backup

to inspect a selected backup and its songs.

## 11. Restore backup

Select:

13. Restore backup

The restore process:

1. Selects an existing backup.
2. Displays its contents.
3. Reads the current playlist.
4. Requires RESTORE confirmation.
5. Creates a safety backup of the current playlist.
6. Removes the current playlist contents.
7. Adds the songs stored in the selected backup.

If the safety backup fails, the restore operation is cancelled.

A backup is restored to the playlist ID stored inside that backup.

## 12. Dry-run mode

Run:

python3 clean_playlist.py --dry-run

Dry-run mode prevents playlist mutations.

Delete operations show what would happen instead of changing YouTube Music.

Manual backup creation and restore are also prevented from making changes while dry-run mode is active.

## 13. Security

Never commit or share:

browser.json
browser_clean.json

The backups/ directory is also ignored by Git.

Backups may contain playlist information and should be treated as local/private data.

## 14. Recommended workflow

1. Configure authentication.
2. Run python3 clean_playlist.py --dry-run.
3. Inspect your playlists.
4. Create a manual backup.
5. Perform a small live operation.
6. Verify the result.
7. Keep important backups until the changes are confirmed.

## 15. Troubleshooting

If authentication fails, refresh the local browser authentication configuration and test again with:

python3 clean_playlist.py --dry-run

Never upload authentication cookies, authorization headers, tokens, or other private credentials to GitHub.
