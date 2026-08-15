#!/usr/bin/env python3

import json
import re
import shlex
import sys
from pathlib import Path

OUTPUT = Path("browser.json")

REQUIRED = {
    "cookie",
    "authorization",
    "user-agent",
}


def add_header(headers, key, value):
    key = key.strip().lower()
    value = value.strip()

    if not key or not value:
        return

    # Remove surrounding quotes if present.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]

    headers[key] = value


def parse_json(text):
    headers = {}

    try:
        data = json.loads(text)
    except Exception:
        return headers

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                add_header(headers, str(key), value)

    return headers


def parse_header_lines(text):
    headers = {}

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # JSON-style:
        # "user-agent": "Mozilla/5.0 ..."
        match = re.match(
            r'^["\']?([^"\':]+)["\']?\s*:\s*["\'](.*)["\']\s*,?$',
            line,
        )

        if match:
            add_header(headers, match.group(1), match.group(2))
            continue

        # Normal header:
        # user-agent: Mozilla/5.0 ...
        if ":" in line:
            key, value = line.split(":", 1)

            key = key.strip().strip("\"'")
            value = value.strip().rstrip(",")

            # Skip obvious non-header JSON/debug lines.
            if key and not key.startswith("{"):
                add_header(headers, key, value)

    return headers


def parse_curl(text):
    headers = {}

    try:
        tokens = shlex.split(text)
    except Exception:
        return headers

    for i, token in enumerate(tokens):
        if token in ("-H", "--header") and i + 1 < len(tokens):
            header = tokens[i + 1]

            if ":" in header:
                key, value = header.split(":", 1)
                add_header(headers, key, value)

    return headers


print("=" * 72)
print("          YOUTUBE MUSIC AUTHENTICATION SETUP")
print("=" * 72)
print()
print("Paste the COMPLETE Request Headers here.")
print()
print("Source:")
print("YouTube Music -> Ctrl+Shift+I -> Network")
print("-> open your playlist -> browse")
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

# 1. Try complete JSON first.
headers.update(parse_json(raw))

# 2. Parse normal / JSON-style header lines.
headers.update(parse_header_lines(raw))

# 3. Parse cURL-style headers if present.
headers.update(parse_curl(raw))

missing = [
    key for key in REQUIRED
    if not headers.get(key)
]

if missing:
    print("\nERROR: Required headers were not found:")

    for key in missing:
        print(f"  - {key}")

    print("\nHeaders detected by the parser:")

    if headers:
        for key in sorted(headers):
            print(f"  - {key}")
    else:
        print("  NONE")

    print("\nMake sure you copied Request Headers from:")
    print("/youtubei/v1/browse?prettyPrint=false")

    sys.exit(1)

# Keep only actual HTTP headers.
# This also removes accidental DevTools metadata.
headers = {
    key: value
    for key, value in headers.items()
    if isinstance(key, str)
    and isinstance(value, str)
    and key not in {
        "decoded",
        "music.youtube.com",
    }
}

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(
        headers,
        f,
        indent=2,
        ensure_ascii=False,
    )

print()
print("=" * 72)
print("SUCCESS — browser.json created")
print("=" * 72)
print()
print(f"File: {OUTPUT.resolve()}")
print(f"Headers detected: {len(headers)}")
print()
print("Required authentication headers:")
print("  cookie        : YES")
print("  authorization : YES")
print("  user-agent    : YES")
print()
print("browser.json is local-only.")
print("It is excluded from Git by .gitignore.")
print()
