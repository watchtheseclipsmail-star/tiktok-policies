#!/usr/bin/env python3
"""
Production-grade clip automation system.

Usage:
    python main.py --channels channel1,channel2 --interval 60 --mode run
    python main.py --channels channel1 --mode once
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure we have data directory
os.makedirs('data', exist_ok=True)
os.makedirs('clips', exist_ok=True)
os.makedirs('logs', exist_ok=True)

from db import init_db
from scheduler import ClipScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/clips.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Twitch clip to TikTok automation')
    parser.add_argument('--channels', required=True, help='Comma-separated Twitch channels (e.g., "channel1,channel2")')
    parser.add_argument('--interval', type=int, default=60, help='Polling interval in minutes (default 60)')
    parser.add_argument('--mode', choices=['run', 'once'], default='run', 
                        help='run=continuous scheduler, once=fetch clips once')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no TikTok upload)')
    parser.add_argument('--whisper-model', default='small', 
                        help='Whisper model size (tiny, base, small, medium, large)')
    
    # Twitch credentials
    parser.add_argument('--twitch-client-id', default=os.getenv('TWITCH_CLIENT_ID'))
    parser.add_argument('--twitch-client-secret', default=os.getenv('TWITCH_CLIENT_SECRET'))
    
    # TikTok credentials
    parser.add_argument('--tiktok-access-token', default=os.getenv('TIKTOK_ACCESS_TOKEN'))
    parser.add_argument('--tiktok-upload-url', default=os.getenv('TIKTOK_UPLOAD_URL'))
    parser.add_argument('--tiktok-publish-url', default=os.getenv('TIKTOK_PUBLISH_URL'))
    
    args = parser.parse_args()
    
    # Validate required credentials
    if not args.twitch_client_id or not args.twitch_client_secret:
        logger.error('TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET are required')
        sys.exit(1)
    
    # Initialize database
    init_db()
    
    # Parse channels
    channels = [ch.strip() for ch in args.channels.split(',')]
    logger.info(f"Configured channels: {channels}")
    
    # Create scheduler
    scheduler = ClipScheduler(
        twitch_client_id=args.twitch_client_id,
        twitch_client_secret=args.twitch_client_secret,
        channels=channels,
        tiktok_access_token=args.tiktok_access_token,
        tiktok_upload_url=args.tiktok_upload_url,
        tiktok_publish_url=args.tiktok_publish_url,
        dry_run=args.dry_run
    )
    
    logger.info(f"Dry run mode: {args.dry_run}")
    
    # Run in requested mode
    if args.mode == 'once':
        logger.info("Running once...")
        scheduler.run_once()
    else:
        logger.info(f"Starting scheduler (interval: {args.interval} minutes)")
        scheduler.start(interval_minutes=args.interval)
        try:
            logger.info("Scheduler is running. Press Ctrl+C to stop.")
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            scheduler.stop()
            sys.exit(0)

if __name__ == '__main__':
    main()
