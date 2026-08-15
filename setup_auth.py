#!/usr/bin/env python3

import json
import sys
from pathlib import Path

OUTPUT = Path("browser.json")

print("=" * 72)
print("          YOUTUBE MUSIC AUTHENTICATION SETUP")
print("=" * 72)
print()
print("Paste the COMPLETE Request Headers copied from:")
print()
print("YouTube Music -> Ctrl+Shift+I -> Network -> browse")
print("/youtubei/v1/browse?prettyPrint=false")
print("-> Headers -> Request Headers")
print()
print("After pasting everything, press Ctrl+D.")
print()
print("-" * 72)

raw = sys.stdin.read()

if not raw.strip():
    print("\nERROR: Nothing was pasted.")
    sys.exit(1)

headers = {}

for line in raw.splitlines():
    line = line.strip()

    if not line:
        continue

    # Ignore browser/devtools sections that aren't headers.
    if line.startswith(":"):
        continue

    if ":" not in line:
        continue

    key, value = line.split(":", 1)

    key = key.strip().lower()
    value = value.strip()

    if not key or not value:
        continue

    headers[key] = value

required = [
    "cookie",
    "authorization",
    "user-agent",
]

missing = [
    key for key in required
    if not headers.get(key)
]

if missing:
    print("\nERROR: Required headers were not found:")
    for key in missing:
        print(f"  - {key}")

    print("\nMake sure you copied the Request Headers section")
    print("from the /youtubei/v1/browse request.")
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
print("Detected required authentication:")
print("  cookie        : YES")
print("  authorization : YES")
print("  user-agent    : YES")
print()
print("browser.json is local-only and is excluded by .gitignore.")
print()
