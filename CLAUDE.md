# Video Search — YouTube Transcript Search Tool

## What this project does

Searches YouTube video transcripts for keyword mentions, returning timestamps with clickable links.

This file does not restate global rules — read `~/.claude/CLAUDE.md` first.

## Prerequisites

- `yt-dlp` installed (`brew install yt-dlp`)
- Python 3.10+
- No pip dependencies needed — uses yt-dlp CLI and stdlib only

## How to use

When the user gives you a YouTube URL and a search term:

1. **Extract captions** using `find_mentions.py`:
   ```bash
   python find_mentions.py "YOUTUBE_URL" "search term" --browser brave
   ```

2. If YouTube blocks unauthenticated requests, use `--browser` to pass cookies:
   ```bash
   python find_mentions.py "YOUTUBE_URL" "search term" --browser brave
   ```
   Supported browsers: `brave`, `chrome`, `firefox`, `safari`

3. If no matches are found, **auto-captions often mangle names** (especially non-English proper nouns). In that case:
   - Dump the full transcript: `python find_mentions.py "URL" --dump --browser brave`
   - Search the dumped `transcript_VIDEOID.txt` for partial/fuzzy matches using grep
   - Try shorter prefixes of the search term (e.g. first 5-6 characters)
   - If still nothing, read the transcript file and scan for phonetically similar words — ASR may have substituted something entirely different

4. **Language**: defaults to Ukrainian (`uk`). Change with `--lang`:
   ```bash
   python find_mentions.py "URL" "term" --lang en --browser brave
   ```

## Common flags

| Flag | Description |
|------|-------------|
| `--dump` | Save full transcript to `transcript_VIDEOID.txt` |
| `--lang LANG` | Caption language code (default: `uk`) |
| `--browser NAME` | Browser to extract cookies from for YouTube auth |
| `--context N` | Number of context lines around each match (default: 2) |

## Troubleshooting

- **"Sign in to confirm you're not a bot"** → use `--browser` flag
- **Zero results but name should be there** → dump transcript and search with partial match or scan for phonetically similar words
- **No captions for language** → try `--lang en` or `--lang ru` as fallback
