# Tests

This directory is reserved for automated tests.

Tests should verify playlist-cleaning logic without modifying a real YouTube Music playlist.

Examples:

- Target song found
- Target song not found
- Target is first song
- Target is last song
- Songs after target are selected correctly
- Empty playlist
- Duplicate song titles
- Authentication/API errors are handled cleanly

Real account credentials should never be used in automated tests.
