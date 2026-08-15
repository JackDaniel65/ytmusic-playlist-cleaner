# Setup Guide

## Requirements

You need:

- Python 3
- pip
- Internet connection
- A YouTube Music account
- Your own YouTube Music authentication
- Git (only needed if cloning/updating the project)

---

## 1. Clone the project

    git clone <GITHUB_REPOSITORY_URL>

Then:

    cd ytmusic-playlist-cleaner

---

## 2. Create a virtual environment

Linux/macOS:

    python3 -m venv venv

Activate it:

    source venv/bin/activate

---

## 3. Install dependencies

    pip install -r requirements.txt

---

## 4. Authentication

You must authenticate with YOUR OWN YouTube Music account.

Do not copy another user's authentication file.

The authentication file must remain local and must never be committed to Git.

---

## 5. Configure the playlist

Use your own playlist ID.

Example:

    PLxxxxxxxxxxxxxxxx

Do not use the original developer's playlist ID.

---

## 6. Choose the last song to keep

Example:

    Take Me to the Beach (feat. Ado)

The program will keep that song and remove songs after it.

---

## 7. Test before making changes

Use a dry-run/test mode if supported by the current version of the program.

The purpose is to verify:

    Playlist
    Target song
    Target position
    Number of songs that would be removed

before making actual changes.

---

## 8. Run

Follow the command shown by the project's README/CLI.

---

## Security

Never publish:

- browser_clean.json
- browser.json
- cookies
- authentication headers
- tokens
- passwords
- `.env` files containing secrets

If credentials are accidentally committed, remove them immediately and invalidate/refresh the affected credentials.
