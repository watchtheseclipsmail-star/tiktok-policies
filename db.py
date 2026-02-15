import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Create SQLite database in the data directory
DB_PATH = os.getenv('DATABASE_URL', 'sqlite:///./data/clips.db')
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False} if 'sqlite' in DB_PATH else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ProcessedClip(Base):
    """Track clips that have been processed to avoid duplicates."""
    __tablename__ = 'processed_clips'
    
    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(String, unique=True, index=True, nullable=False)
    clip_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    broadcaster = Column(String, nullable=False)  # Twitch channel/creator name
    tiktok_video_id = Column(String, nullable=True)  # TikTok video ID if uploaded
    tiktok_url = Column(String, nullable=True)  # TikTok video URL
    status = Column(String, default='pending')  # pending, processing, uploaded, failed
    error_message = Column(String, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    """Track scheduler job runs."""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, nullable=False)  # 'fetch_clips', 'process_queue', etc.
    last_run = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database (create tables if they don't exist)."""
    Base.metadata.create_all(bind=engine)
    print('Database initialized')

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
