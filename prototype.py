#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import subprocess
import json
from pathlib import Path

# Minimal prototype that:
# - Gets Twitch app token
# - Finds broadcaster id for a channel
# - Fetches recent clips and picks the top by view_count
# - Downloads clip via yt-dlp
# - Transcribes with whisper Python package
# - Writes SRT and burns subtitles while reformatting to 9:16 via ffmpeg

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_BASE = "https://api.twitch.tv/helix"

def get_app_token(client_id, client_secret):
    resp = requests.post(TWITCH_TOKEN_URL, data={
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    })
    resp.raise_for_status()
    return resp.json()['access_token']

def get_user_id(client_id, token, login):
    headers = {'Client-ID': client_id, 'Authorization': f'Bearer {token}'}
    resp = requests.get(f"{TWITCH_API_BASE}/users", params={'login': login}, headers=headers)
    resp.raise_for_status()
    data = resp.json().get('data', [])
    if not data:
        raise RuntimeError(f"User {login} not found")
    return data[0]['id']

def get_top_clip_for_broadcaster(client_id, token, broadcaster_id, first=5):
    headers = {'Client-ID': client_id, 'Authorization': f'Bearer {token}'}
    params = {'broadcaster_id': broadcaster_id, 'first': first}
    resp = requests.get(f"{TWITCH_API_BASE}/clips", params=params, headers=headers)
    resp.raise_for_status()
    clips = resp.json().get('data', [])
    if not clips:
        raise RuntimeError('No clips found')
    clips.sort(key=lambda c: c.get('view_count', 0), reverse=True)
    return clips[0]

def download_clip(clip_url, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['yt-dlp', '-f', 'best', '-o', str(out_path), clip_url]
    print('Running:', ' '.join(cmd))
    subprocess.check_call(cmd)
    return out_path

def transcribe_with_whisper(input_path, model_name='small'):
    try:
        import whisper
    except Exception as e:
        print('Failed to import whisper:', e)
        raise
    model = whisper.load_model(model_name)
    print('Transcribing (this may take a while) with model:', model_name)
    result = model.transcribe(str(input_path))
    # result contains 'segments' with start/end/text
    return result

def write_srt(segments, srt_path):
    def fmt_time(t):
        h = int(t//3600)
        m = int((t%3600)//60)
        s = int(t%60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, start=1):
            start = fmt_time(seg['start'])
            end = fmt_time(seg['end'])
            text = seg['text'].strip().replace('-->', '->')
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

def reformat_and_burn_subs(input_path, srt_path, output_path):
    # 9:16 vertical 1080x1920, scale and pad, then burn subtitles
    vf = "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles={}:force_style='FontName=Arial,FontSize=48'".format(srt_path.replace('\\', '\\\\'))
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path), '-vf', vf,
        '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '128k', str(output_path)
    ]
    print('Running ffmpeg to reformat and burn subtitles...')
    subprocess.check_call(cmd)
    return output_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', help='Twitch channel login', required=True)
    parser.add_argument('--client-id', default=os.getenv('TWITCH_CLIENT_ID'))
    parser.add_argument('--client-secret', default=os.getenv('TWITCH_CLIENT_SECRET'))
    parser.add_argument('--out', default='out.mp4')
    parser.add_argument('--model', default='small', help='Whisper model name (tiny, base, small, medium, large)')
    parser.add_argument('--tiktok', action='store_true', help='Enable TikTok upload (requires further config)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode: do not perform network uploads (default False)')
    parser.add_argument('--tiktok-access-token', default=os.getenv('TIKTOK_ACCESS_TOKEN'))
    parser.add_argument('--tiktok-upload-url', default=os.getenv('TIKTOK_UPLOAD_URL'))
    parser.add_argument('--tiktok-publish-url', default=os.getenv('TIKTOK_PUBLISH_URL'))
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print('TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET are required (env or args)')
        sys.exit(2)

    token = get_app_token(args.client_id, args.client_secret)
    user_id = get_user_id(args.client_id, token, args.channel)
    clip = get_top_clip_for_broadcaster(args.client_id, token, user_id, first=10)
    print('Selected clip:', clip.get('title'), clip.get('url'), 'views:', clip.get('view_count'))

    workdir = Path('clips')
    workdir.mkdir(exist_ok=True)
    clip_path = workdir / 'clip.mp4'
    downloaded = download_clip(clip['url'], clip_path)

    result = transcribe_with_whisper(downloaded, model_name=args.model)
    segments = result.get('segments', [])
    if not segments:
        print('No segments returned from transcription; writing full transcript as one segment')
        segments = [{'start': 0.0, 'end': result.get('duration', 0.0), 'text': result.get('text', '')}]

    srt_path = workdir / 'clip.srt'
    write_srt(segments, srt_path)

    out = Path(args.out)
    reformat_and_burn_subs(downloaded, str(srt_path), out)
    print('Output written to', out)

    # TikTok upload (optional)
    if args.tiktok:
        from tiktok_client import TikTokClient
        dry = args.dry_run
        client = TikTokClient(dry_run=dry, access_token=args.tiktok_access_token,
                              upload_url=args.tiktok_upload_url, publish_url=args.tiktok_publish_url)
        print('TikTok mode enabled. dry_run=', dry)
        resp = client.upload_video(out, title=f"Clip from {args.channel}")
        print('TikTok upload response:', resp)

if __name__ == '__main__':
    main()
