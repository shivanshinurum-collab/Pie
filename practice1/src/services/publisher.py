import json
import os
import time
import requests
from sqlalchemy.orm import Session
from src.config import settings, logger
from src.database import PublicationLog, Meme

class InstagramPublisherService:
    def __init__(self, db: Session):
        self.db = db
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.ig_account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.api_version = "v19.0"
        self.base_url = "https://graph.facebook.com"

    def _publish_mock(self, meme_id: str, image_url_or_path: str, caption: str) -> str:
        """Mock publisher saving logs locally. Used for development and testing."""
        logger.info("[MOCK PUBLISH] Simulating Instagram Publish...")
        logger.info(f"Targeting Meme ID: {meme_id}")
        logger.info(f"Image Source: {image_url_or_path}")
        logger.info(f"Caption Length: {len(caption)} characters")
        
        # Simulate small network delay
        time.sleep(1.0)
        
        # Save to local mock tracker file
        log_file = os.path.join(settings.LOCAL_STORAGE_DIR, "published_posts.json")
        mock_post_id = f"ig_mock_{int(time.time())}"
        
        post_record = {
            "post_id": mock_post_id,
            "meme_id": meme_id,
            "published_at": time.asctime(),
            "image": image_url_or_path,
            "caption": caption
        }
        
        try:
            records = []
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    records = json.load(f)
            records.append(post_record)
            with open(log_file, "w") as f:
                json.dump(records, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to write mock post tracker file: {str(e)}")
            
        return mock_post_id

    def create_media_container(self, media_url: str, caption: str, is_video: bool = False) -> str | None:
        """Step 1: Create a media container for image or video. Returns container creation_id."""
        url = f"{self.base_url}/{self.api_version}/{self.ig_account_id}/media"
        payload = {
            "caption": caption,
            "access_token": self.access_token
        }
        
        if is_video:
            payload["media_type"] = "REELS"
            payload["video_url"] = media_url
        else:
            payload["image_url"] = media_url
            
        try:
            response = requests.post(url, data=payload, timeout=20)
            res_data = response.json()
            if response.status_code == 200:
                creation_id = res_data.get("id")
                logger.info(f"Successfully created Instagram container. Creation ID: {creation_id}")
                return creation_id
            else:
                logger.error(f"Instagram container creation failed: {res_data}")
        except Exception as e:
            logger.error(f"HTTP request failed during Instagram container creation: {str(e)}")
        return None

    def check_container_status(self, creation_id: str) -> bool:
        """Step 2: Check status of video reels containers (compilation check)."""
        url = f"{self.base_url}/{self.api_version}/{creation_id}"
        params = {
            "fields": "status_code,status",
            "access_token": self.access_token
        }
        
        # Max wait 3 minutes, checking every 10 seconds
        for _ in range(18):
            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                status_code = data.get("status_code")
                logger.info(f"Checking Reel container status: {status_code}")
                if status_code == "FINISHED":
                    return True
                elif status_code == "ERROR":
                    logger.error(f"Reel container compilation failed: {data.get('status')}")
                    return False
            except Exception as e:
                logger.error(f"Error checking container status: {str(e)}")
            time.sleep(10)
        return False

    def publish_container(self, creation_id: str) -> str | None:
        """Step 3: Publish container on Instagram page. Returns post_id."""
        url = f"{self.base_url}/{self.api_version}/{self.ig_account_id}/media_publish"
        payload = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        try:
            response = requests.post(url, data=payload, timeout=20)
            res_data = response.json()
            if response.status_code == 200:
                post_id = res_data.get("id")
                logger.info(f"Successfully published on Instagram. Post ID: {post_id}")
                return post_id
            else:
                logger.error(f"Instagram publish failed: {res_data}")
        except Exception as e:
            logger.error(f"HTTP request failed during Instagram publish: {str(e)}")
        return None

    def publish_meme_post(self, meme_id: str, media_url: str, caption: str, is_video: bool = False) -> bool:
        """Publishes meme to Instagram with full container handling and DB logging."""
        # Query meme
        meme = self.db.query(Meme).filter(Meme.id == meme_id).first()
        if not meme:
            logger.error(f"Meme ID {meme_id} not found in database.")
            return False
            
        success = False
        post_id = None
        error_msg = None
        
        # Determine if we should run mock publish or live publish
        is_live = bool(self.access_token and self.ig_account_id and media_url.startswith("http"))
        
        try:
            if is_live:
                # Retries for live publish container creation
                creation_id = None
                for attempt in range(3):
                    creation_id = self.create_media_container(media_url, caption, is_video)
                    if creation_id:
                        break
                    logger.warning(f"Container creation failed, retrying in 5 seconds (attempt {attempt+1}/3)...")
                    time.sleep(5)
                
                if creation_id:
                    # Video reels need status compilation checks
                    status_ready = True
                    if is_video:
                        status_ready = self.check_container_status(creation_id)
                        
                    if status_ready:
                        post_id = self.publish_container(creation_id)
                        if post_id:
                            success = True
                        else:
                            error_msg = "Publish container endpoint failed."
                    else:
                        error_msg = "Reel video processing timeout or compilation error."
                else:
                    error_msg = "Failed to create media container."
            else:
                # Run mock simulation
                post_id = self._publish_mock(meme_id, media_url, caption)
                success = True
                
        except Exception as e:
            error_msg = f"Unexpected publisher error: {str(e)}"
            logger.error(error_msg)
            
        # Log to Database
        log = PublicationLog(
            meme_id=meme_id,
            platform="instagram",
            status="success" if success else "failed",
            external_post_id=post_id,
            error_message=error_msg
        )
        self.db.add(log)
        
        if success:
            meme.meme_status = "published"
        else:
            meme.meme_status = "publishing_failed"
            
        self.db.commit()
        return success
