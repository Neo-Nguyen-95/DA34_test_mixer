from pathlib import Path

path = Path("tiad_debug/main_bundle.js")

js = path.read_text(
    encoding="utf-8",
    errors="ignore",
)

keywords = [
    "x-dpad-response-public-key",
    "dpad-response",
    "response-public-key",
    "ECDH",
    "deriveKey",
    "deriveBits",
    "subtle.decrypt",
    "crypto.subtle",
    "importKey",
    "exportKey",
]

for keyword in keywords:
    print("\n" + "=" * 100)
    print("SEARCH:", keyword)

    start = 0
    found = False

    while True:
        pos = js.lower().find(
            keyword.lower(),
            start,
        )

        if pos == -1:
            break

        found = True

        print("\nPOSITION:", pos)
        print("-" * 100)

        snippet = js[
            max(0, pos - 2000):
            min(len(js), pos + 4000)
        ]

        print(snippet)

        start = pos + len(keyword)

    if not found:
        print("NOT FOUND")