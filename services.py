import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import requests
import subprocess

logger = logging.getLogger(__name__)

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_BASE = "https://api.twitch.tv/helix"

class TwitchService:
    """Handle Twitch API interactions."""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
    
    def get_app_token(self):
        """Fetch an OAuth app token."""
        if self.token:
            return self.token
        resp = requests.post(TWITCH_TOKEN_URL, data={
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        })
        resp.raise_for_status()
        self.token = resp.json()['access_token']
        return self.token
    
    def get_user_id(self, login):
        """Get broadcaster ID from login name."""
        token = self.get_app_token()
        headers = {'Client-ID': self.client_id, 'Authorization': f'Bearer {token}'}
        resp = requests.get(f"{TWITCH_API_BASE}/users", params={'login': login}, headers=headers)
        resp.raise_for_status()
        data = resp.json().get('data', [])
        if not data:
            raise RuntimeError(f"User {login} not found")
        return data[0]['id']
    
    def get_top_clips(self, broadcaster_id, first=5):
        """Fetch recent clips for a broadcaster, sorted by views."""
        token = self.get_app_token()
        headers = {'Client-ID': self.client_id, 'Authorization': f'Bearer {token}'}
        params = {'broadcaster_id': broadcaster_id, 'first': first}
        resp = requests.get(f"{TWITCH_API_BASE}/clips", params=params, headers=headers)
        resp.raise_for_status()
        clips = resp.json().get('data', [])
        clips.sort(key=lambda c: c.get('view_count', 0), reverse=True)
        return clips

class ClipProcessor:
    """Handle clip downloading, transcription, and formatting."""
    
    def __init__(self, work_dir='./clips', whisper_model='small'):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model = whisper_model
    
    def download_clip(self, clip_url, clip_id):
        """Download a clip using yt-dlp."""
        out_path = self.work_dir / f"{clip_id}.mp4"
        if out_path.exists():
            logger.info(f"Clip {clip_id} already downloaded")
            return out_path
        
        cmd = ['yt-dlp', '-f', 'best', '-o', str(out_path), clip_url]
        logger.info(f"Downloading clip {clip_id} from {clip_url}")
        subprocess.check_call(cmd)
        return out_path
    
    def transcribe(self, video_path):
        """Transcribe video using whisper."""
        try:
            import whisper
        except ImportError:
            logger.error("whisper not installed")
            raise
        
        logger.info(f"Transcribing {video_path} with model {self.whisper_model}")
        model = whisper.load_model(self.whisper_model)
        result = model.transcribe(str(video_path))
        return result
    
    def write_srt(self, segments, srt_path):
        """Write SRT subtitle file from segments."""
        def fmt_time(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t - int(t)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, start=1):
                start = fmt_time(seg['start'])
                end = fmt_time(seg['end'])
                text = seg['text'].strip().replace('-->', '->')
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        
        logger.info(f"Wrote SRT to {srt_path}")
    
    def reformat_to_vertical(self, input_path, srt_path, output_path):
        """Reformat to 9:16 vertical and burn subtitles."""
        vf = f"scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles={srt_path}:force_style='FontName=Arial,FontSize=48'"
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path), '-vf', vf,
            '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
            '-c:a', 'aac', '-b:a', '128k', str(output_path)
        ]
        logger.info(f"Reformatting to vertical and burning subtitles -> {output_path}")
        subprocess.check_call(cmd)
        return output_path
    
    def process_clip(self, clip_url, clip_id, title):
        """Full pipeline: download -> transcribe -> reformat."""
        try:
            video_path = self.download_clip(clip_url, clip_id)
            result = self.transcribe(video_path)
            segments = result.get('segments', [])
            if not segments:
                segments = [{'start': 0.0, 'end': result.get('duration', 0.0), 'text': result.get('text', '')}]
            
            srt_path = self.work_dir / f"{clip_id}.srt"
            self.write_srt(segments, srt_path)
            
            output_path = self.work_dir / f"{clip_id}_tiktok.mp4"
            self.reformat_to_vertical(video_path, str(srt_path), output_path)
            
            return output_path
        except Exception as e:
            logger.error(f"Error processing clip {clip_id}: {e}")
            raise
