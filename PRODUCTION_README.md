# StreamClipAutoReposter – Production Edition

Automated system for monitoring Twitch streamers, downloading their popular clips, adding captions with AI, and posting to TikTok.

## Features

✅ **Automatic clip detection** – Periodically fetches top clips from configured Twitch channels  
✅ **AI captions** – Uses OpenAI Whisper for speech-to-text transcription  
✅ **Vertical formatting** – Automatically reformats to 9:16 (TikTok-ready)  
✅ **Scheduled uploads** – Posts to TikTok on a configurable schedule  
✅ **Duplicate prevention** – Tracks processed clips in SQLite to avoid reprocessing  
✅ **Error handling & retries** – Graceful handling of API failures and transient errors  
✅ **Logging** – Comprehensive logs for debugging and monitoring  
✅ **Docker support** – Easy deployment with Docker and Docker Compose  

## Prerequisites

### System Requirements
- Python 3.9+
- `ffmpeg` (for video processing)
- ~2 GB free disk space (for clips and SQLite DB)
- Internet connection

### API Credentials
1. **Twitch Developer App** → [developer.twitch.tv](https://developer.twitch.tv)
   - Get `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET`
   
2. **TikTok Content Publishing API** → [developer.tiktok.com](https://developer.tiktok.com)
   - Apply with `TIKTOK_TERMS_OF_SERVICE.html` and `TIKTOK_PRIVACY_POLICY.html`
   - After approval: `TIKTOK_ACCESS_TOKEN`, `TIKTOK_UPLOAD_URL`, `TIKTOK_PUBLISH_URL`

## Installation

### Option 1: Local Installation (for development/testing)

```bash
git clone https://github.com/watchtheseclipsmail-star/tiktok-policies.git
cd tiktok-policies
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Option 2: Docker Installation (recommended for production)

```bash
docker build -t tiktok-clip-bot .
```

## Configuration

### 1. Create `.env` file

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your Twitch and TikTok credentials
```

### 2. Configure channels

Edit the `TWITCH_CHANNELS` variable in `.env`:

```
TWITCH_CHANNELS=ninja,pokimane,shroud
```

### 3. Test mode (dry-run)

Before going live, test with `DRY_RUN=true` in `.env`. This will:
- Fetch clips normally
- Process (transcribe, reformat) normally
- **Skip TikTok upload** (dry-run logs instead)

## Usage

### Local (development)

```bash
# Run once (fetch and process clips)
python main.py --channels ninja,pokimane --mode once --dry-run

# Run as continuous scheduler (every 60 minutes)
python main.py --channels ninja,pokimane --interval 60 --mode run
```

### Docker

```bash
# Run once
docker run --rm \
  -e TWITCH_CLIENT_ID="your_id" \
  -e TWITCH_CLIENT_SECRET="your_secret" \
  -e TWITCH_CHANNELS="ninja,pokimane" \
  -v $(pwd)/data:/app/data \
  tiktok-clip-bot --mode once --dry-run

# Run as background service (docker-compose recommended)
docker-compose up -d
```

### Docker Compose (easiest for production)

```bash
# 1. Create .env with your credentials
cp .env.example .env
# Edit .env

# 2. Start the service
docker-compose up -d

# 3. Monitor logs
docker-compose logs -f

# 4. Stop the service
docker-compose down
```

## Database & Tracking

The system uses **SQLite** (built-in, zero setup) to track:
- Processed clips (avoid duplicates)
- Upload status and timestamps
- Error messages for failed uploads

Database file: `./data/clips.db` (created automatically)

To inspect the database:

```bash
sqlite3 data/clips.db
> SELECT * FROM processed_clips;
> .quit
```

## Logging

Logs are written to:
- **Console** (stdout/stderr) – for immediate feedback
- **File** – `clips.log` in the working directory

Change the log level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # for verbose logs
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--channels` | *required* | Comma-separated Twitch channel names |
| `--interval` | 60 | Minutes between clip fetches |
| `--mode` | run | `run` for continuous, `once` for single execution |
| `--dry-run` | false | Dry-run mode (skip TikTok upload) |
| `--whisper-model` | small | Whisper model size (tiny, base, small, medium, large) |

### Larger Whisper models (better accuracy, slower)

```bash
# Use 'medium' model (better quality, ~1-2 min per clip)
python main.py --channels ninja,pokimane --whisper-model medium --mode once
```

**Trade-offs:**
- `tiny` – fastest, lowest accuracy
- `small` – good balance (recommended)
- `medium` – better accuracy, slower
- `large` – best accuracy, requires GPU for speed

## Troubleshooting

### "TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET are required"
→ Check your `.env` file is in the same directory as `main.py`, or set env vars:
```bash
export TWITCH_CLIENT_ID="..."
export TWITCH_CLIENT_SECRET="..."
python main.py --channels ninja --mode once
```

### "User {channel} not found"
→ Check the channel name is correct (case-sensitive sometimes on Twitch API)

### "No clips found"
→ The selected channel may have no recent clips. Try a different channel or increase the `--interval`.

### Clip processing is slow
→ You're likely using Whisper without GPU. Options:
- Use a smaller model: `--whisper-model tiny` or `--whisper-model base`
- Or add GPU support (NVIDIA only): see **GPU Acceleration** below

### TikTok upload fails
→ Check:
1. `TIKTOK_ACCESS_TOKEN` is valid (tokens can expire)
2. `TIKTOK_UPLOAD_URL` and `TIKTOK_PUBLISH_URL` are correct
3. Run in `--dry-run` mode to verify clip processing works
4. Check `clips.log` for detailed error messages

## Advanced Setup

### GPU Acceleration (NVIDIA only)

To use GPU with Whisper for 5–10x faster transcription:

```bash
# Install CUDA (for your GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Then run with larger model
python main.py --channels ninja,pokimane --whisper-model medium --mode run
```

### PostgreSQL (for scaling)

To use PostgreSQL instead of SQLite (recommended for 100+ clips/day):

```bash
# 1. Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/clips_db

# 2. Install package
pip install psycopg2-binary

# 3. Create database
createdb clips_db

# 4. Run
python main.py --channels ninja,pokimane --mode run
```

## Monitoring & Maintenance

### Check processed clips

```bash
sqlite3 data/clips.db "SELECT clip_id, broadcaster, status, processed_at FROM processed_clips LIMIT 10;"
```

### View errors

```bash
grep -i error clips.log | tail -20
```

### Manual cleanup

```bash
# Delete processed clips older than 30 days
sqlite3 data/clips.db "DELETE FROM processed_clips WHERE processed_at < datetime('now', '-30 days');"

# Delete local clip files
rm -f clips/*
```

## Compliance & Legal

⚠️ **Important:**
1. **Always attribute creators** in clip titles/descriptions
2. **Get streamer permission** before reposting at scale (to avoid DMCA takedowns)
3. **Follow TikTok and Twitch ToS** – do not violate rate limits or spam
4. **Monitor for takedown requests** and remove content promptly
5. **Keep your tokens secure** – never share API credentials

See `TIKTOK_TERMS_OF_SERVICE.html` and `TIKTOK_PRIVACY_POLICY.html` for details.

## Support

- **Issues?** Check `clips.log` for detailed errors
- **API questions?** See [Twitch Docs](https://dev.twitch.tv/docs) and [TikTok Docs](https://developers.tiktok.com/doc/en)
- **Code issues?** File an issue on GitHub

## License

MIT License – See LICENSE file
