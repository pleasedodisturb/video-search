#!/usr/bin/env python3
"""Find mentions of a search term in YouTube video transcripts.

Downloads auto-captions via yt-dlp, then searches for keyword occurrences
with timestamps and clickable YouTube links.

Usage:
    python find_mentions.py VIDEO_URL_OR_ID SEARCH_TERM [--dump] [--context N] [--lang LANG]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile


CONTEXT_LINES = 2
DEFAULT_LANG = "uk"


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from a YouTube URL or return as-is if already an ID."""
    if "youtube.com" in url_or_id or "youtu.be" in url_or_id:
        match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url_or_id)
        if match:
            return match.group(1)
        print("Could not extract video ID from URL", file=sys.stderr)
        sys.exit(1)
    return url_or_id


def fetch_transcript(video_id: str, lang: str = DEFAULT_LANG, browser: str | None = None) -> list[dict]:
    """Fetch auto-captions via yt-dlp and parse into timestamped entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = os.path.join(tmpdir, "%(id)s")
        cmd = [
            "yt-dlp",
            "--write-auto-subs",
            "--sub-lang", lang,
            "--sub-format", "json3",
            "--skip-download",
            "-o", out_template,
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        if browser:
            cmd[1:1] = ["--cookies-from-browser", browser]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"yt-dlp error:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        json3_path = os.path.join(tmpdir, f"{video_id}.{lang}.json3")
        if not os.path.exists(json3_path):
            print(f"No captions found for language '{lang}'", file=sys.stderr)
            sys.exit(1)

        with open(json3_path, encoding="utf-8") as f:
            data = json.load(f)

    entries = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if not text:
            continue
        entries.append({"start": ev.get("tStartMs", 0) / 1000.0, "text": text})

    return entries


def format_timestamp(seconds: float) -> str:
    """Convert seconds to H:MM:SS or M:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def make_youtube_link(video_id: str, seconds: float) -> str:
    """Create a timestamped YouTube URL."""
    return f"https://www.youtube.com/watch?v={video_id}&t={int(seconds)}s"


def search_transcript(entries: list[dict], term: str, context: int = CONTEXT_LINES):
    """Search transcript entries for a term, returning matches with context."""
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    matches = []

    for i, entry in enumerate(entries):
        if pattern.search(entry["text"]):
            start = max(0, i - context)
            end = min(len(entries), i + context + 1)
            matches.append((i, entry, entries[start:end]))

    return matches


def dump_transcript(entries: list[dict], output_path: str):
    """Save full transcript to a text file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            ts = format_timestamp(entry["start"])
            f.write(f"[{ts}] {entry['text']}\n")
    print(f"Transcript saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Find mentions in YouTube video transcripts")
    parser.add_argument("video", help="YouTube video URL or ID")
    parser.add_argument("search_term", nargs="?", help="Term to search for (case-insensitive)")
    parser.add_argument("--dump", action="store_true", help="Save full transcript to file")
    parser.add_argument("--context", type=int, default=CONTEXT_LINES, help="Context lines around each match (default: 2)")
    parser.add_argument("--lang", default=DEFAULT_LANG, help="Caption language code (default: uk)")
    parser.add_argument("--browser", default=None, help="Browser to extract cookies from (e.g. brave, chrome, firefox)")
    args = parser.parse_args()

    video_id = extract_video_id(args.video)

    print(f"Fetching {args.lang} captions for {video_id}...")
    entries = fetch_transcript(video_id, lang=args.lang, browser=args.browser)
    print(f"Got {len(entries)} transcript segments\n")

    if args.dump:
        output_path = f"transcript_{video_id}.txt"
        dump_transcript(entries, output_path)
        if not args.search_term:
            return

    if not args.search_term:
        parser.error("search_term is required unless --dump is used")

    matches = search_transcript(entries, args.search_term, args.context)

    if not matches:
        print(f'No matches found for "{args.search_term}"')
        print("\nTip: Auto-captions often mangle names. Try:")
        print(f"  python find_mentions.py {args.video} --dump --lang {args.lang}")
        print(f"  Then grep the transcript for a partial match.")
        return

    print(f'Found {len(matches)} mention(s) of "{args.search_term}":\n')
    print("=" * 60)

    for idx, (i, entry, context_entries) in enumerate(matches, 1):
        ts = format_timestamp(entry["start"])
        link = make_youtube_link(video_id, entry["start"])

        print(f"\n  Match {idx} — [{ts}]")
        print(f"  {link}\n")

        for ctx in context_entries:
            ctx_ts = format_timestamp(ctx["start"])
            marker = ">>>" if ctx is entry else "   "
            print(f"  {marker} [{ctx_ts}] {ctx['text']}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
