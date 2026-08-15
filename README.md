# YouTube Music Playlist Cleaner

A Python tool for cleaning a YouTube Music playlist by keeping songs up to a selected song and removing everything after it.

## What it does

The program finds a selected song in a playlist and removes every song that comes after it.

## Setup

1. Clone this repository.
2. Create a Python virtual environment.
3. Install the dependencies with `pip install -r requirements.txt`.
4. Create your own `browser.json` authentication file using `browser.example.json` as a reference.
5. Follow `docs/SETUP.md` for the complete setup instructions.

## Important security note

`browser.json` and `browser_clean.json` contain private YouTube Music authentication information and are intentionally excluded from Git.

Never upload your real authentication files to GitHub.

## Documentation

- `docs/SETUP.md` - setup instructions
- `docs/HOW_IT_WORKS.md` - simple explanation of how the project works
- `docs/TROUBLESHOOTING.md` - common problems and fixes
- `tests/README.md` - testing information
