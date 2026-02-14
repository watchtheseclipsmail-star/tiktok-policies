Prototype: Twitch → TikTok-ready clip

This prototype fetches a top clip from a Twitch channel, downloads it, transcribes it with OpenAI Whisper, and reformats it to a 9:16 MP4 suitable for TikTok.

Prerequisites
- Python 3.9+
- `ffmpeg` installed and on PATH
- `yt-dlp` installed (the Python package is included in requirements but system-wide is fine)
- Optional: GPU and CUDA for faster Whisper models

Install

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Environment variables
- `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` – from your Twitch developer app
- `TWITCH_CHANNEL` – the channel login name to poll for clips

Run

```bash
python prototype.py --channel <channel> --out out.mp4
```

Notes
- This prototype does not post to TikTok. It outputs `out.mp4` ready for manual upload.
- If you prefer cloud STT, replace the transcription section accordingly.
