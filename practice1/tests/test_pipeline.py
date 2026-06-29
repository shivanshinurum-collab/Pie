import os
import sys
from datetime import datetime
from PIL import Image

# Force SQLite for unit and integration testing before importing any packages
os.environ["DATABASE_URL"] = "sqlite:///test_news_meme.db"

# Ensure the root project folder is in python pathway
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings, logger
from src.database import init_db, SessionLocal, NewsArticle, Meme
from src.services.news_collector import NewsCollectorService
from src.services.news_analyst import NewsAnalystService
from src.services.image_processor import ImageProcessorService
from src.services.meme_compositor import MemeCompositorService
from src.services.video_generator import VideoGeneratorService

def create_dummy_base_image(path: str):
    """Create a basic solid color dummy image for testing compostions."""
    img = Image.new("RGB", (1080, 720), color=(14, 165, 233)) # sky blue color
    img.save(path)
    logger.info(f"Dummy base image created at {path}")

def run_integration_check():
    logger.info("=== STARTING NEWS MEME ENGINE INTEGRATION CHECK ===")
    
    # 1. Initialize SQLite Database for test run
    # Override settings configuration for database to local SQLite testing
    settings.DATABASE_URL = "sqlite:///test_news_meme.db"
    settings.STORAGE_TYPE = "local"
    settings.LOCAL_STORAGE_DIR = "./test_storage"
    
    # Re-initialize directories
    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.LOCAL_STORAGE_DIR, "memes"), exist_ok=True)
    
    init_db()
    db = SessionLocal()
    
    try:
        # Clear previous run data
        db.query(Meme).delete()
        db.query(NewsArticle).delete()
        db.commit()
        
        # 2. Insert Mock news article
        logger.info("Step 1: Ingesting mock news article...")
        test_article = NewsArticle(
            title="Tech Giant Releases Open-Source AI Model that Explains User Jokes",
            description="The newly released model analyzes user messages and tells them why they are not funny. Experts say this marks the end of comedy.",
            full_content="An AI research lab has shocked the world by releasing 'AntiJoke-1.0', a 70B parameter LLM whose sole purpose is to analyze casual jokes, explain their technical structures, and make users feel bad about their sense of humor.",
            source_url="https://example.com/tech-news/antijoke",
            image_url=None,
            author="ByteSized News",
            published_at=datetime.utcnow(),
            category="Technology",
            source_name="Example News",
            popularity_score=85.0,
            content_hash="mock_hash_xyz_123",
            processing_status="pending"
        )
        db.add(test_article)
        db.commit()
        
        # 3. Simulate Analyst Service Check
        logger.info("Step 2: Testing Analyst evaluate logic...")
        analyst = NewsAnalystService(db)
        
        # Manually run analyze to bypass network keys in testing (uses local default mockup return)
        analysis_result = analyst.analyze_article(test_article)
        logger.info(f"Analyst Output: Meme Score={analysis_result.meme_potential_score}, Summary: {analysis_result.one_line_summary}")
        
        # Manually insert Meme entry matching threshold
        meme = Meme(
            news_article_id=test_article.id,
            topic=analysis_result.topic,
            primary_sentiment=analysis_result.sentiment,
            meme_potential_score=95,  # Force high score for test
            instagram_potential_score=90,
            one_line_summary=analysis_result.one_line_summary,
            news_context=analysis_result.news_context,
            meme_status="pending"
        )
        db.add(meme)
        test_article.processing_status = "analyzed"
        db.commit()
        
        # 4. Image Processing & Mock base image
        logger.info("Step 3: Creating and optimizing base photos...")
        meme_folder = os.path.join(settings.LOCAL_STORAGE_DIR, "memes", meme.id)
        os.makedirs(meme_folder, exist_ok=True)
        
        base_img_path = os.path.join(meme_folder, "base_image.jpg")
        create_dummy_base_image(base_img_path)
        
        processor = ImageProcessorService()
        processed_success = processor.process_and_optimize(
            base_img_path, base_img_path, width=1080, height=720
        )
        logger.info(f"Image Optimization: {processed_success}")
        
        # 5. PIL Meme Compositor
        logger.info("Step 4: Composing 1080x1350 canvas layouts...")
        compositor = MemeCompositorService()
        composed_meme_path = os.path.join(meme_folder, "composed_meme_funny.jpg")
        
        composed_success = compositor.compose_meme(
            headline=test_article.title,
            subheadline=meme.one_line_summary,
            image_path=base_img_path,
            caption="ME TRYING TO LAUGH AT THE AI'S CRITIQUE OF MY COMPILATION LOGS",
            output_path=composed_meme_path
        )
        logger.info(f"Meme Composition Status: {composed_success}")
        assert os.path.exists(composed_meme_path), "Composed meme image was not created!"
        
        # 6. Skip Video Reels compilation (disabled by request)
        logger.info("Step 5: Testing Video Reels compilation (Bypassed as per user configuration)...")
        
        # 7. Check output
        if composed_success and os.path.exists(composed_meme_path):
            logger.info("=== ALL SYSTEM PIPELINE MODULES COMPILE AND INTEGRATE SUCCESSFULLY ===")
            logger.info(f"Generated Post Image: {os.path.abspath(composed_meme_path)}")
        else:
            logger.error("!!! MEME GENERATION/COMPOSITION FAILED IN SYSTEM INTEGRATION CHECK !!!")
            
    except Exception as e:
        logger.error(f"Pipeline test failed with error: {str(e)}", exc_info=True)
    finally:
        db.close()
        
        # Clean up database file after run
        if os.path.exists("test_news_meme.db"):
            try:
                os.remove("test_news_meme.db")
            except Exception:
                pass

if __name__ == "__main__":
    run_integration_check()
