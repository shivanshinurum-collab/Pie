import os
import re
import urllib.parse
from PIL import Image, ImageEnhance, ImageChops
import requests
from src.config import settings, logger

class ImageProcessorService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }

    def download_image(self, url: str, save_path: str) -> bool:
        """Download image from url and save locally."""
        try:
            logger.info(f"Downloading image from {url}...")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                logger.warning(f"Failed to download image. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
        return False

    def remove_borders(self, img: Image.Image) -> Image.Image:
        """Autocrop solid borders (white or black) from image edges using bounding boxes."""
        # Find bounding box for non-black content
        bg_black = Image.new(img.mode, img.size, (0, 0, 0))
        diff_black = ImageChops.difference(img, bg_black)
        diff_black = ImageChops.add(diff_black, diff_black, 2.0, -100)
        bbox_black = diff_black.getbbox()
        
        # Find bounding box for non-white content
        bg_white = Image.new(img.mode, img.size, (255, 255, 255))
        diff_white = ImageChops.difference(img, bg_white)
        diff_white = ImageChops.add(diff_white, diff_white, 2.0, -100)
        bbox_white = diff_white.getbbox()

        bbox = bbox_black or bbox_white
        if bbox:
            logger.info(f"Autocropping borders from bounding box: {bbox}")
            return img.crop(bbox)
        return img

    def crop_to_aspect_ratio(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Centroid cropping to target aspect ratio."""
        curr_w, curr_h = img.size
        target_aspect = target_w / target_h
        curr_aspect = curr_w / curr_h
        
        if curr_aspect > target_aspect:
            # Current image is wider than target. Crop left & right.
            new_w = int(curr_h * target_aspect)
            left = (curr_w - new_w) // 2
            right = left + new_w
            img = img.crop((left, 0, right, curr_h))
        elif curr_aspect < target_aspect:
            # Current image is taller than target. Crop top & bottom.
            new_h = int(curr_w / target_aspect)
            top = (curr_h - new_h) // 2
            bottom = top + new_h
            img = img.crop((0, top, curr_w, bottom))
            
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def enhance_image(self, img: Image.Image) -> Image.Image:
        """Enhance image color, contrast, and sharpness for professional look."""
        # Sharpness
        sharpener = ImageEnhance.Sharpness(img)
        img = sharpener.enhance(1.4)
        
        # Contrast
        contraster = ImageEnhance.Contrast(img)
        img = contraster.enhance(1.1)
        
        # Color saturation
        colorer = ImageEnhance.Color(img)
        img = colorer.enhance(1.1)
        
        return img

    def process_and_optimize(self, source_path: str, target_path: str, width: int = 1080, height: int = 720) -> bool:
        """Full pipeline: load, strip borders, crop, enhance, and save."""
        try:
            with Image.open(source_path) as img:
                img = img.convert("RGB")
                img = self.remove_borders(img)
                img = self.crop_to_aspect_ratio(img, width, height)
                img = self.enhance_image(img)
                img.save(target_path, "JPEG", quality=95)
                logger.info(f"Image processed successfully and saved to {target_path}")
                return True
        except Exception as e:
            logger.error(f"Error processing image {source_path}: {str(e)}")
            return False

    def search_copyright_free_image(self, query: str) -> str | None:
        """Search DuckDuckGo Images to retrieve a free URL for the query."""
        logger.info(f"Searching free images for query: {query}")
        try:
            # Use DuckDuckGo images endpoint (vqd query resolution)
            url = f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(query + ' free copyright image')}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                # Basic search for images in HTML tags (standard fallbacks)
                img_urls = re.findall(r'img_d.*?=(http.*?)&', response.text)
                if not img_urls:
                    # Alternative regex check for standard link references
                    img_urls = re.findall(r'href="(https?://[^"]+\.(?:jpg|jpeg|png))"', response.text)
                
                # Filter out standard tracking/pixel links
                valid_urls = [urllib.parse.unquote(u) for u in img_urls if "duckduckgo" not in u and "yandex" not in u]
                if valid_urls:
                    logger.info(f"Found search image: {valid_urls[0]}")
                    return valid_urls[0]
        except Exception as e:
            logger.error(f"DuckDuckGo image search failed: {str(e)}")
        
        # Fallback to LoremFlickr for dynamic keyword-based images
        logger.warning("Falling back to LoremFlickr random search query placeholder.")
        words = re.findall(r'\b\w{3,10}\b', query.lower())
        stop_words = {"free", "copyright", "image", "news", "with", "after", "about", "under", "these", "their", "there"}
        keywords = [w for w in words if w not in stop_words][:3]
        keywords_str = ",".join(keywords) if keywords else "news"
        return f"https://loremflickr.com/1080/720/{keywords_str}"
