# How This Project Works — Simple Explanation

## What does this project do?

This project cleans a YouTube Music playlist.

You tell it:

> "Keep everything up to this song."

For example:

    Song 1
    Song 2
    Song 3
    Take Me to the Beach (feat. Ado)
    Song 5
    Song 6
    Song 7

If the target is:

    Take Me to the Beach (feat. Ado)

the program keeps:

    Song 1
    Song 2
    Song 3
    Take Me to the Beach (feat. Ado)

and removes everything after it.

---

## How does it work?

The basic flow is:

    YouTube Music
          ↓
    Authentication
          ↓
    Get playlist
          ↓
    Read songs
          ↓
    Find target song
          ↓
    Find its position
          ↓
    Keep everything before/including target
          ↓
    Select everything after target
          ↓
    Ask for confirmation
          ↓
    Remove selected songs
          ↓
    Playlist is updated

---

## 1. Authentication

YouTube Music needs to know which account is making the request.

The project uses `ytmusicapi` for this.

The authentication information is stored locally.

IMPORTANT:

Never upload your authentication file to GitHub.

It can contain information that allows access to your account.

---

## 2. Getting the playlist

The program receives a playlist ID.

A YouTube Music URL looks something like:

    https://music.youtube.com/playlist?list=PLxxxxxxxx

The important part is:

    PLxxxxxxxx

That is the playlist ID.

The program asks YouTube Music for the playlist.

---

## 3. Finding the target song

The program reads the songs one by one.

For example:

    1. Song A
    2. Song B
    3. Song C
    4. Take Me to the Beach (feat. Ado)
    5. Song E

It finds the target at position 4.

---

## 4. Deciding what to keep

If the target is #4:

    KEEP:
    1
    2
    3
    4

    REMOVE:
    5
    6
    7
    ...
    LAST SONG

The target song itself is NOT removed.

---

## 5. Removing songs

YouTube Music identifies playlist entries using information such as:

    videoId
    setVideoId

The program uses those identifiers to tell YouTube Music which playlist entries should be removed.

---

## 6. Why authentication is needed

The program is changing YOUR playlist.

It therefore needs permission to access the account and modify the playlist.

This is why authentication is required.

---

## 7. What is ytmusicapi?

`ytmusicapi` is the Python library used by this project to communicate with YouTube Music.

The project does not directly implement the entire YouTube Music API itself.

Instead:

    Our Python code
          ↓
    ytmusicapi
          ↓
    YouTube Music
          ↓
    Your playlist

---

## 8. What happened during development?

We encountered several errors while making the original project.

### JSONDecodeError

We saw:

    JSONDecodeError:
    Expecting value: line 1 column 1

This happened because YouTube Music returned an HTTP error page instead of the JSON response the library expected.

In other words:

    Program expected:
    JSON

    YouTube returned:
    HTML error page

So JSON parsing failed.

---

### AttributeError

We also encountered:

    AttributeError:
    'YTMusic' object has no attribute 'base_url'

This came from trying to inspect/use an internal attribute that wasn't available in the installed version of the library.

The final project should avoid depending on undocumented internal attributes.

---

### DKMS / rtl8192eu errors

There were also many errors involving:

    rtl8192eu
    DKMS
    Linux kernel
    linux-headers

These were NOT errors in this project.

They were Kali Linux kernel/module configuration problems happening while packages were being installed.

They have nothing to do with playlist cleaning.

---

## 9. Why browser_clean.json isn't included

The authentication file belongs to the individual user.

It is NOT project source code.

Every person using this project must create their own authentication setup.

Never use somebody else's authentication file.

---

## 10. Simple example

Suppose a playlist contains 500 songs.

Target:

    Take Me to the Beach (feat. Ado)

Target position:

    125

Then:

    Total songs: 500
    Keep: 125
    Remove: 375

The program removes:

    #126 → #500

The final playlist ends at:

    #125 Take Me to the Beach (feat. Ado)

---

## Important warning

This program changes a real playlist.

Always understand what will be removed before confirming.

Do not upload authentication files, cookies, tokens, or other private credentials to GitHub.
