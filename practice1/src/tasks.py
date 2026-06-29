import os
from celery import Celery
from celery.schedules import crontab
from src.config import settings, logger
from src.database import SessionLocal, init_db, NewsArticle, Meme, MemeVariation, MemeCaption, MemeReel
from src.services.news_collector import NewsCollectorService
from src.services.news_analyst import NewsAnalystService
from src.services.image_processor import ImageProcessorService
from src.services.image_generator import ImageGeneratorService
from src.services.meme_compositor import MemeCompositorService
from src.services.caption_generator import CaptionGeneratorService
from src.services.video_generator import VideoGeneratorService
from src.services.publisher import InstagramPublisherService

# Initialize Celery app
celery_app = Celery("news_meme_tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Configure Celery (e.g. tracking task results)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Setup Periodic Scheduler (Celery Beat)
celery_app.conf.beat_schedule = {
    "autonomous-news-run-every-15-mins": {
        "task": "src.tasks.collect_news_task",
        "schedule": crontab(minute=f"*/{settings.NEWS_CHECK_INTERVAL_MINS}"),
    }
}

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Initialize DB tables on startup
    init_db()

# -------------------------------------------------------------
# TASK DEFINITIONS
# -------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def collect_news_task(self):
    """Step 1: Collect latest news articles from various sources."""
    logger.info("Starting Celery Task: collect_news_task")
    db = SessionLocal()
    try:
        collector = NewsCollectorService(db)
        new_articles_count = collector.collect_and_save()
        logger.info(f"News collection finished. Ingested {new_articles_count} new unique articles.")
        
        # Trigger the next step (Analysis) automatically if new articles are found
        if new_articles_count > 0:
            analyze_news_task.delay()
    except Exception as exc:
        logger.error(f"Error in collect_news_task: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_news_task(self):
    """Step 2: AI evaluates news items for meme/viral compatibility."""
    logger.info("Starting Celery Task: analyze_news_task")
    db = SessionLocal()
    try:
        analyst = NewsAnalystService(db)
        analyzed_count = analyst.process_pending_articles()
        logger.info(f"AI news analysis finished. Evaluated {analyzed_count} articles.")
        
        # Trigger meme asset generation if we have pending memes in DB
        pending_memes = db.query(Meme).filter(Meme.meme_status == "pending").count()
        if pending_memes > 0:
            generate_meme_assets_task.delay()
    except Exception as exc:
        logger.error(f"Error in analyze_news_task: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def generate_meme_assets_task(self):
    """Dispatcher task: Queries pending memes and spawns asynchronous parallel tasks to process them."""
    logger.info("Starting Celery Task: generate_meme_assets_task (Dispatcher)")
    db = SessionLocal()
    try:
        pending_memes = db.query(Meme).filter(Meme.meme_status == "pending").all()
        logger.info(f"Found {len(pending_memes)} pending memes to dispatch.")
        for meme in pending_memes:
            process_single_meme_assets_task.delay(meme.id)
    except Exception as exc:
        logger.error(f"Error in generate_meme_assets_task dispatcher: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def process_single_meme_assets_task(self, meme_id: str):
    """Processes asset generation for a single meme: resolves image, generates captions, composes canvas, and queues publishing."""
    logger.info(f"Starting Celery Task: process_single_meme_assets_task for Meme ID: {meme_id}")
    db = SessionLocal()
    
    img_processor = ImageProcessorService()
    img_generator = ImageGeneratorService()
    meme_compositor = MemeCompositorService()
    caption_generator = CaptionGeneratorService()
    
    try:
        meme = db.query(Meme).filter(Meme.id == meme_id).first()
        if not meme:
            logger.error(f"Meme ID {meme_id} not found in database.")
            return
            
        if meme.meme_status != "pending":
            logger.info(f"Meme ID {meme_id} is already in status {meme.meme_status}. Skipping asset generation.")
            return
            
        article = meme.article
        
        # Create isolated folders for this meme inside our local storage
        meme_folder = os.path.join(settings.LOCAL_STORAGE_DIR, "memes", meme.id)
        os.makedirs(meme_folder, exist_ok=True)
        
        # Step A: Resolve Base Image Source
        base_image_local_path = os.path.join(meme_folder, "base_image.jpg")
        image_resolved = False
        
        if article.image_url:
            # Attempt to download and crop original news image
            downloaded = img_processor.download_image(article.image_url, base_image_local_path)
            if downloaded:
                # Optimize, remove borders, enhance
                image_resolved = img_processor.process_and_optimize(
                    base_image_local_path, base_image_local_path, width=1080, height=720
                )
        
        if not image_resolved:
            # Search DDG copyright safe images if article didn't have one
            search_url = img_processor.search_copyright_free_image(article.title)
            if search_url:
                downloaded = img_processor.download_image(search_url, base_image_local_path)
                if downloaded:
                    image_resolved = img_processor.process_and_optimize(
                        base_image_local_path, base_image_local_path, width=1080, height=720
                    )
                    
        if not image_resolved:
            # Generate AI illustration (FLUX/DALL-E) as final fallback
            image_resolved = img_generator.generate_image(
                article.title, article.description or "", base_image_local_path
            )
            
        if not image_resolved:
            logger.error(f"Could not resolve image for Meme {meme.id}. Skipping.")
            meme.meme_status = "generation_failed"
            db.commit()
            return
            
        # Step B: Perform Image Understanding (if original image exists)
        img_desc = ""
        if article.image_url:
            img_desc = img_generator.analyze_image_with_gemini(base_image_local_path)
            
        # Step C: AI Generate Captions, Hashtags, Hooks, and Meme Reaction variants
        ai_captions = caption_generator.generate_all_captions(
            article.title, meme.one_line_summary, meme.news_context, img_desc
        )
        
        # Step D: Save captions to Database
        # Save Instagram main copy
        ig_pkg = ai_captions.instagram
        ig_caption_text = f"{ig_pkg.hook}\n\n{ig_pkg.post_caption}\n\n{ig_pkg.cta}\n\n" + " ".join(ig_pkg.hashtags)
        
        # Save the multiple styles captions
        for cap in ai_captions.captions:
            db_cap = MemeCaption(
                meme_id=meme.id,
                category=cap.length,
                humor_style=cap.style.lower(),
                caption_text=cap.text,
                hashtags=" ".join(ig_pkg.hashtags)
            )
            db.add(db_cap)
            
        # Step E: Compose Image Meme (1080x1350) - Only 1 primary style (funny)
        primary_composed_path = ""
        caption_text = ai_captions.variations.funny
        composed_path = os.path.join(meme_folder, "composed_meme_funny.jpg")
        
        composed_success = meme_compositor.compose_meme(
            headline=article.title,
            subheadline=meme.one_line_summary,
            image_path=base_image_local_path,
            caption=caption_text,
            output_path=composed_path
        )
        
        if composed_success:
            primary_composed_path = composed_path
            # Save variation in DB
            db_var = MemeVariation(
                meme_id=meme.id,
                style="funny",
                base_image_path=base_image_local_path,
                composed_image_path=primary_composed_path,
                prompt_used=caption_text
            )
            db.add(db_var)
        else:
            logger.error(f"Could not compose primary meme for Meme {meme.id}. Skipping.")
            meme.meme_status = "generation_failed"
            db.commit()
            return
            
        # Step F: Generate Video Reels (5s, 10s, 15s durations) - REMOVED AS REQUESTED BY USER!
        
        # Step G: Update Meme status
        meme.meme_status = "generated"
        logger.info(f"Meme assets generated successfully for Meme ID: {meme.id}")
        
        # Trigger Auto Publisher Task for this meme
        publish_meme_task.delay(meme.id, primary_composed_path, ig_caption_text)
        
        db.commit()
    except Exception as exc:
        logger.error(f"Error in process_single_meme_assets_task: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=180)
def publish_meme_task(self, meme_id: str, media_url_or_path: str, caption: str, is_video: bool = False):
    """Step 9: Publish meme directly to Instagram."""
    logger.info(f"Starting Celery Task: publish_meme_task for Meme ID: {meme_id}")
    db = SessionLocal()
    try:
        publisher = InstagramPublisherService(db)
        success = publisher.publish_meme_post(
            meme_id=meme_id,
            media_url=media_url_or_path,
            caption=caption,
            is_video=is_video
        )
        if success:
            logger.info(f"Instagram publish completed successfully for Meme ID: {meme_id}")
        else:
            logger.error(f"Instagram publish failed for Meme ID: {meme_id}")
    except Exception as exc:
        logger.error(f"Error in publish_meme_task: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
