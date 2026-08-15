# Troubleshooting

## JSONDecodeError

Example:

    JSONDecodeError:
    Expecting value: line 1 column 1

Possible cause:

YouTube Music returned an error page instead of JSON.

Check authentication first.

---

## Authentication problems

If requests start returning HTTP 400/401/403 errors:

1. Check that your authentication is still valid.
2. Re-authenticate using your own account.
3. Make sure the authentication file is in the expected location.
4. Make sure you did not accidentally copy an old/expired session.

---

## `base_url` AttributeError

If you see:

    'YTMusic' object has no attribute 'base_url'

do not add random attributes to the library object.

Check the installed `ytmusicapi` version and use the public API supported by that version.

---

## DKMS / rtl8192eu

Errors mentioning:

    rtl8192eu
    DKMS
    linux-headers
    linux-image

are Linux kernel/driver problems.

They are unrelated to the playlist cleaner.

---

## No songs found

Check:

- Playlist ID
- Authentication
- Playlist visibility
- Whether the authenticated account owns/has access to the playlist

---

## Target song not found

Check the exact title.

YouTube Music may return a title with differences in:

- capitalization
- punctuation
- spaces
- featured artist formatting
- additional text

---

## Important

Never paste authentication cookies, authorization headers, tokens, or other private credentials into GitHub issues or public chats.
