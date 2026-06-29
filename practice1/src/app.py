import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from src.config import settings, logger
from src.database import get_db, init_db, NewsArticle, Meme, MemeVariation, MemeCaption, MemeReel, PublicationLog
from src.tasks import collect_news_task, analyze_news_task, generate_meme_assets_task

app = FastAPI(
    title=settings.APP_NAME,
    description="REST API and Control Dashboard for the Autonomous AI News Meme Engine",
    version="1.0.0"
)

# Enable CORS for frontend dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage directories exist and mount for static asset serving
os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.LOCAL_STORAGE_DIR), name="static")

@app.on_event("startup")
def on_startup():
    # Setup database tables
    init_db()

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    """Engine status endpoint returning database statistics."""
    try:
        news_count = db.query(NewsArticle).count()
        meme_count = db.query(Meme).count()
        published_count = db.query(Meme).filter(Meme.meme_status == "published").count()
        failed_count = db.query(Meme).filter(Meme.meme_status == "publishing_failed").count()
        
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "environment": settings.ENV,
            "statistics": {
                "total_news_articles": news_count,
                "total_memes_created": meme_count,
                "successfully_published": published_count,
                "failed_publications": failed_count
            }
        }
    except Exception as e:
        logger.error(f"Root healthcheck failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

# -------------------------------------------------------------
# CONTROL TRIGGER ENDPOINTS
# -------------------------------------------------------------

@app.post("/api/v1/trigger/collect")
def trigger_collection():
    """Manually trigger the news collection Celery task."""
    task = collect_news_task.delay()
    return {"message": "News collection triggered", "task_id": task.id}

@app.post("/api/v1/trigger/analyze")
def trigger_analysis():
    """Manually trigger the news analysis Celery task."""
    task = analyze_news_task.delay()
    return {"message": "News analysis triggered", "task_id": task.id}

@app.post("/api/v1/trigger/generate")
def trigger_generation():
    """Manually trigger the meme asset generation Celery task."""
    task = generate_meme_assets_task.delay()
    return {"message": "Meme asset generation triggered", "task_id": task.id}

# -------------------------------------------------------------
# QUERY ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/v1/news")
def list_news(limit: int = 50, db: Session = Depends(get_db)):
    """List scraped news articles."""
    articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit).all()
    return articles

@app.get("/api/v1/memes")
def list_memes(limit: int = 50, db: Session = Depends(get_db)):
    """List generated memes with statuses."""
    memes = db.query(Meme).order_by(Meme.created_at.desc()).limit(limit).all()
    
    response = []
    for m in memes:
        response.append({
            "id": m.id,
            "topic": m.topic,
            "sentiment": m.primary_sentiment,
            "meme_potential_score": m.meme_potential_score,
            "instagram_potential_score": m.instagram_potential_score,
            "one_line_summary": m.one_line_summary,
            "status": m.meme_status,
            "created_at": m.created_at,
            "article_title": m.article.title if m.article else "Unknown"
        })
    return response

@app.get("/api/v1/memes/{meme_id}")
def get_meme_details(meme_id: str, db: Session = Depends(get_db)):
    """Get full asset package for a specific meme."""
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
        
    variations = db.query(MemeVariation).filter(MemeVariation.meme_id == meme_id).all()
    captions = db.query(MemeCaption).filter(MemeCaption.meme_id == meme_id).all()
    reels = db.query(MemeReel).filter(MemeReel.meme_id == meme_id).all()
    publications = db.query(PublicationLog).filter(PublicationLog.meme_id == meme_id).all()
    
    # Helper to convert local paths to HTTP server static links
    def to_static_url(path: str) -> str:
        if not path:
            return ""
        if path.startswith("http"):
            return path
        # Replace local storage dir prefix with server url pattern
        rel_path = os.path.relpath(path, settings.LOCAL_STORAGE_DIR)
        return f"/static/{rel_path}"

    return {
        "id": meme.id,
        "topic": meme.topic,
        "one_line_summary": meme.one_line_summary,
        "context": meme.news_context,
        "status": meme.meme_status,
        "article": {
            "title": meme.article.title,
            "url": meme.article.source_url,
            "original_image": meme.article.image_url
        },
        "variations": [
            {
                "id": v.id,
                "style": v.style,
                "url": to_static_url(v.composed_image_path),
                "text": v.prompt_used
            } for v in variations
        ],
        "captions": [
            {
                "style": c.humor_style,
                "length": c.category,
                "text": c.caption_text
            } for c in captions
        ],
        "reels": [
            {
                "id": r.id,
                "duration": r.duration,
                "video_url": to_static_url(r.video_path),
                "script": r.voiceover_script,
                "music_vibe": r.music_category
            } for r in reels
        ],
        "publications": publications
    }

@app.get("/api/v1/publications")
def list_publication_logs(limit: int = 50, db: Session = Depends(get_db)):
    """List publication history and errors."""
    logs = db.query(PublicationLog).order_by(PublicationLog.published_at.desc()).limit(limit).all()
    return logs
