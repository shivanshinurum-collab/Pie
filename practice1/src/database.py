import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Text, Float, DateTime, 
    Integer, ForeignKey, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from src.config import settings, logger

Base = declarative_base()

# Dynamic UUID type helper for database compatibility (Postgres UUID vs SQLite String)
class GUID(String):
    pass

def get_db_engine():
    db_url = settings.DATABASE_URL
    try:
        # Check if database is sqlite or postgresql
        if db_url.startswith("postgresql"):
            # Attempt postgres connection with connection pooling options
            engine = create_engine(
                db_url, 
                pool_size=10, 
                max_overflow=20, 
                pool_recycle=3600
            )
        else:
            engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.warning(f"Failed to connect to database URL: {db_url}. Falling back to SQLite local db.")
        sqlite_fallback = "sqlite:///local_news_meme.db"
        return create_engine(sqlite_fallback, connect_args={"check_same_thread": False})

engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------
# DATABASE MODELS
# -------------------------------------------------------------

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=False)
    image_url = Column(String(1000), nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    category = Column(String(100), nullable=True)
    source_name = Column(String(255), nullable=True)
    popularity_score = Column(Float, default=0.0)
    language = Column(String(10), default="en")
    country = Column(String(10), default="US")
    content_hash = Column(String(64), unique=True, nullable=False)
    processing_status = Column(String(50), default="pending")  # pending, analyzed, failed, skipped
    created_at = Column(DateTime, default=datetime.utcnow)
    
    memes = relationship("Meme", back_populates="article", cascade="all, delete-orphan")


class Meme(Base):
    __tablename__ = "memes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    news_article_id = Column(String(36), ForeignKey("news_articles.id"), nullable=False)
    topic = Column(String(255), nullable=True)
    primary_sentiment = Column(String(50), nullable=True)
    meme_potential_score = Column(Integer, default=0)
    instagram_potential_score = Column(Integer, default=0)
    one_line_summary = Column(Text, nullable=True)
    news_context = Column(Text, nullable=True)
    meme_status = Column(String(50), default="pending")  # pending, generated, publishing_failed, published
    created_at = Column(DateTime, default=datetime.utcnow)
    
    article = relationship("NewsArticle", back_populates="memes")
    variations = relationship("MemeVariation", back_populates="meme", cascade="all, delete-orphan")
    captions = relationship("MemeCaption", back_populates="meme", cascade="all, delete-orphan")
    reels = relationship("MemeReel", back_populates="meme", cascade="all, delete-orphan")
    publications = relationship("PublicationLog", back_populates="meme", cascade="all, delete-orphan")


class MemeVariation(Base):
    __tablename__ = "meme_variations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meme_id = Column(String(36), ForeignKey("memes.id"), nullable=False)
    style = Column(String(50), nullable=False)  # funny, savage, dark, wholesome, sarcastic
    base_image_path = Column(String(1000), nullable=True)  # Downloaded or AI gen base
    composed_image_path = Column(String(1000), nullable=True)  # 1080x1350 meme canvas
    prompt_used = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meme = relationship("Meme", back_populates="variations")


class MemeCaption(Base):
    __tablename__ = "meme_captions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meme_id = Column(String(36), ForeignKey("memes.id"), nullable=False)
    category = Column(String(50), nullable=False)  # short, long
    humor_style = Column(String(50), nullable=False)  # indian, global, gen_z, dark, sports, political
    caption_text = Column(Text, nullable=False)
    hashtags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meme = relationship("Meme", back_populates="captions")


class MemeReel(Base):
    __tablename__ = "meme_reels"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meme_id = Column(String(36), ForeignKey("memes.id"), nullable=False)
    duration = Column(Integer, default=5)  # 5, 10, 15
    video_path = Column(String(1000), nullable=False)
    voiceover_script = Column(Text, nullable=True)
    music_category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meme = relationship("Meme", back_populates="reels")


class PublicationLog(Base):
    __tablename__ = "publication_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meme_id = Column(String(36), ForeignKey("memes.id"), nullable=False)
    platform = Column(String(50), default="instagram")
    status = Column(String(50), nullable=False)  # success, failed
    external_post_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    
    meme = relationship("Meme", back_populates="publications")


def init_db():
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete.")
