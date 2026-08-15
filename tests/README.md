# Project Test / Working

## What does this project do?

This project connects to YouTube Music using browser authentication
and can inspect a playlist and remove songs after a selected song.

Example:

Playlist:
1. Song A
2. Song B
3. Take Me to the Beach (feat. Ado)
4. Song D
5. Song E

If the user chooses:

Take Me to the Beach (feat. Ado)

the project keeps songs 1-3 and removes songs 4-5.

## How it works

1. The user logs into YouTube Music in their browser.
2. Browser authentication information is exported into `browser.json`.
3. The Python program loads that authentication information.
4. `ytmusicapi` communicates with YouTube Music.
5. The program reads the playlist.
6. It searches for the selected song.
7. Everything after that song is identified for removal.
8. The program updates the playlist.
9. The user can refresh YouTube Music and see the updated playlist.

## Important

`browser.json` contains private authentication information.

NEVER upload the real `browser.json` to GitHub.

Use `browser.example.json` as the template instead.

## Testing safely

Before modifying a real playlist, use a test playlist containing a few
songs and verify that the program identifies the correct cutoff song.

The project should be tested with a playlist where removing songs is safe.
