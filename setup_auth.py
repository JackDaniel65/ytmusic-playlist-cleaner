#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

OUTPUT = Path("browser.json")

REQUIRED = [
    "cookie",
    "authorization",
    "user-agent",
]


def extract_value(text, key):
    patterns = [
        # JSON:
        rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"',
        # Single-quoted Python-style:
        rf"'{re.escape(key)}'\s*:\s*'((?:\\.|[^'\\])*)'",
        # Normal HTTP header:
        rf'(?im)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            value = match.group(1).strip()

            if value:
                return value

    return None


print("=" * 72)
print("       YOUTUBE MUSIC AUTHENTICATION SETUP")
print("=" * 72)
print()
print("Paste the COMPLETE Request Headers below.")
print()
print("YouTube Music -> Ctrl+Shift+I -> Network")
print("-> open playlist -> browse")
print("-> /youtubei/v1/browse?prettyPrint=false")
print("-> Headers -> Request Headers")
print()
print("When finished, press Ctrl+D.")
print()
print("-" * 72)

raw = sys.stdin.read()

if not raw.strip():
    print("\nERROR: Nothing was pasted.")
    sys.exit(1)

headers = {}

# Extract required headers directly from the complete pasted text.
for key in REQUIRED:
    value = extract_value(raw, key)

    if value:
        headers[key] = value

# Extract additional useful YouTube headers.
OPTIONAL = [
    "accept",
    "accept-encoding",
    "accept-language",
    "content-encoding",
    "content-type",
    "origin",
    "priority",
    "referer",
    "x-browser-channel",
    "x-browser-copyright",
    "x-browser-validation",
    "x-browser-year",
    "x-client-data",
    "x-goog-authuser",
    "x-goog-visitor-id",
    "x-origin",
    "x-youtube-bootstrap-logged-in",
    "x-youtube-client-name",
    "x-youtube-client-version",
]

for key in OPTIONAL:
    value = extract_value(raw, key)

    if value:
        headers[key] = value

missing = [
    key for key in REQUIRED
    if key not in headers
]

if missing:
    print("\nERROR: Required headers were not found:")

    for key in missing:
        print(f"  - {key}")

    print("\nThe parser detected these header names:")

    if headers:
        for key in sorted(headers):
            print(f"  - {key}")
    else:
        print("  NONE")

    print("\nMake sure you copied the Request Headers section")
    print("from:")
    print("/youtubei/v1/browse?prettyPrint=false")

    sys.exit(1)

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(headers, f, indent=2, ensure_ascii=False)

print()
print("=" * 72)
print("SUCCESS")
print("=" * 72)
print()
print(f"Created: {OUTPUT.resolve()}")
print(f"Headers saved: {len(headers)}")
print()
print("Authentication detected:")
print("  cookie        : YES")
print("  authorization : YES")
print("  user-agent    : YES")
print()
print("browser.json is LOCAL ONLY.")
print("It is protected by .gitignore.")
print()
