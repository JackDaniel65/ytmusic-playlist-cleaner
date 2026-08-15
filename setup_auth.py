#!/usr/bin/env python3

import json
import re
import shlex
import sys
from pathlib import Path

OUTPUT = Path("browser.json")

REQUIRED = ["cookie", "authorization", "user-agent"]

JUNK_KEYS = {
    "Decoded",
    "/youtubei/v1/browse?prettyPrint=false",
    "/youtubei/v1/att/get?prettyPrint=false",
}


def clean_headers(data):
    if not isinstance(data, dict):
        return {}

    result = {}

    for key, value in data.items():
        if not isinstance(key, str):
            continue

        if not isinstance(value, str):
            continue

        key = key.strip().strip("\"'").lower()
        value = value.strip()

        if not key or not value:
            continue

        result[key] = value

    return result


def try_json(text):
    candidates = [text.strip()]

    # Sometimes copied data has a leading/trailing code fence.
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.I).strip()
    cleaned = cleaned.rstrip("`").strip()

    if cleaned not in candidates:
        candidates.append(cleaned)

    for candidate in candidates:
        try:
            data = json.loads(candidate)

            if isinstance(data, dict):
                return clean_headers(data)

        except Exception:
            pass

    return {}


def parse_normal_headers(text):
    headers = {}

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # "user-agent": "..."
        match = re.match(
            r'^\s*["\']?([^"\':]+)["\']?\s*:\s*["\'](.*)["\']\s*,?\s*$',
            line,
        )

        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()

            if key and value:
                headers[key.lower()] = value

            continue

        # user-agent: ...
        if ":" in line:
            key, value = line.split(":", 1)

            key = key.strip().strip("\"'")
            value = value.strip().rstrip(",")

            if key and value:
                headers[key.lower()] = value

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

            if ":" not in header:
                continue

            key, value = header.split(":", 1)

            key = key.strip()
            value = value.strip()

            if key and value:
                headers[key.lower()] = value

    return headers


def extract_headers(text):
    headers = {}

    # First: exact JSON object.
    headers.update(try_json(text))

    # Second: ordinary Request Headers.
    headers.update(parse_normal_headers(text))

    # Third: cURL format.
    headers.update(parse_curl(text))

    return headers


print("=" * 72)
print("          YOUTUBE MUSIC AUTHENTICATION SETUP")
print("=" * 72)
print()
print("1. Open YouTube Music and log in.")
print("2. Press Ctrl+Shift+I.")
print("3. Open Network.")
print("4. Open the playlist you want to use.")
print("5. Search Network for: browse")
print("6. Open /youtubei/v1/browse?prettyPrint=false")
print("7. Open Headers.")
print("8. Copy the Request Headers.")
print()
print("Paste the COMPLETE copied data below.")
print("When finished, press Ctrl+D.")
print()
print("-" * 72)

raw = sys.stdin.read()

if not raw.strip():
    print("\nERROR: Nothing was pasted.")
    sys.exit(1)

headers = extract_headers(raw)

missing = [
    key for key in REQUIRED
    if not headers.get(key)
]

if missing:
    print("\nERROR: Could not create a valid authentication file.")
    print()
    print("Required headers missing:")

    for key in missing:
        print("  -", key)

    print()
    print("Header names detected:")

    if headers:
        for key in sorted(headers):
            print("  -", key)
    else:
        print("  NONE")

    print()
    print("Important:")
    print("Copy the Request Headers themselves, not the page HTML")
    print("or the Network request name.")

    sys.exit(1)

# Remove DevTools artifacts while keeping real headers.
headers = {
    key: value
    for key, value in headers.items()
    if key not in {x.lower() for x in JUNK_KEYS}
}

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(headers, f, indent=2, ensure_ascii=False)

print()
print("=" * 72)
print("SUCCESS")
print("=" * 72)
print()
print("Created:", OUTPUT.resolve())
print("Headers saved:", len(headers))
print()
print("Authentication:")
print("  cookie        : YES")
print("  authorization : YES")
print("  user-agent    : YES")
print()
print("browser.json is local only.")
print("It is protected by .gitignore.")
