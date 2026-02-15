import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from db import SessionLocal, ProcessedClip, Job
from services import TwitchService, ClipProcessor
from tiktok_client import TikTokClient

logger = logging.getLogger(__name__)

class ClipScheduler:
    """Manage scheduling of clip fetching, processing, and uploading."""
    
    def __init__(self, twitch_client_id, twitch_client_secret, channels, 
                 tiktok_access_token=None, tiktok_upload_url=None, 
                 tiktok_publish_url=None, dry_run=False):
        self.twitch = TwitchService(twitch_client_id, twitch_client_secret)
        self.processor = ClipProcessor(whisper_model='small')
        self.tiktok = TikTokClient(
            access_token=tiktok_access_token,
            dry_run=dry_run,
            upload_url=tiktok_upload_url,
            publish_url=tiktok_publish_url
        )
        self.channels = channels  # list of Twitch channel names
        self.scheduler = BackgroundScheduler()
    
    def fetch_and_process_clips(self):
        """Fetch new clips from configured channels and process them."""
        db = SessionLocal()
        try:
            for channel in self.channels:
                self._process_channel(db, channel)
        except Exception as e:
            logger.error(f"Error in fetch_and_process_clips: {e}")
        finally:
            db.close()
    
    def _process_channel(self, db: Session, channel):
        """Process clips from a single channel."""
        logger.info(f"Checking channel: {channel}")
        try:
            # Get broadcaster ID
            broadcaster_id = self.twitch.get_user_id(channel)
            
            # Fetch clips
            clips = self.twitch.get_top_clips(broadcaster_id, first=10)
            logger.info(f"Found {len(clips)} clips for {channel}")
            
            for clip in clips:
                clip_id = clip['id']
                
                # Check if already processed
                existing = db.query(ProcessedClip).filter_by(clip_id=clip_id).first()
                if existing:
                    logger.info(f"Clip {clip_id} already processed, skipping")
                    continue
                
                # Record in DB
                processed = ProcessedClip(
                    clip_id=clip_id,
                    clip_url=clip['url'],
                    title=clip['title'],
                    broadcaster=channel,
                    status='processing'
                )
                db.add(processed)
                db.commit()
                
                try:
                    # Process clip
                    output_path = self.processor.process_clip(clip['url'], clip_id, clip['title'])
                    logger.info(f"Processed clip {clip_id}: {output_path}")
                    
                    # Upload to TikTok
                    upload_resp = self.tiktok.upload_video(
                        str(output_path),
                        title=f"{clip['title']} (via {channel})",
                        description=f"Clip from {channel}\n{clip['url']}"
                    )
                    logger.info(f"TikTok upload response: {upload_resp}")
                    
                    # Update DB
                    processed.status = 'uploaded'
                    processed.tiktok_video_id = upload_resp.get('video_id') or upload_resp.get('media_id')
                    processed.uploaded_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Clip {clip_id} uploaded successfully")
                    
                except Exception as e:
                    logger.error(f"Error processing clip {clip_id}: {e}")
                    processed.status = 'failed'
                    processed.error_message = str(e)
                    db.commit()
        
        except Exception as e:
            logger.error(f"Error processing channel {channel}: {e}")
    
    def start(self, interval_minutes=60):
        """Start the scheduler."""
        self.scheduler.add_job(
            self.fetch_and_process_clips,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='fetch_clips',
            name='Fetch and process clips',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info(f"Scheduler started, fetching every {interval_minutes} minutes")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def run_once(self):
        """Run the fetch_and_process_clips job immediately (for testing)."""
        logger.info("Running fetch_and_process_clips once...")
        self.fetch_and_process_clips()
        logger.info("Done")
