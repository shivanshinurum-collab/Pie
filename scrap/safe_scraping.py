import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time
import os
import hashlib
import re
import mimetypes
import io

# ======================
# CONFIG
# ======================
START_URL = "https://about.google/"
MAX_PAGES = 20   # safety limit (change if needed)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

visited = set()
data = []

# Keywords to detect copyright/watermarked/licensed images
COPYRIGHT_KEYWORDS = ["copyright", "watermark", "stock", "shutterstock", "getty", "adobe-stock", "licensed"]


# ======================
# CHECK SAME DOMAIN
# ======================
def is_same_domain(base, url):
    return urlparse(base).netloc == urlparse(url).netloc


# ======================
# SCRAPE PAGE
# ======================
def scrape_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        page_data = {
            "url": url,
            "titles": [],
            "paragraphs": [],
            "images": [],
            "videos": []
        }

        # TEXT
        for tag in soup.find_all(["h1", "h2", "h3"]):
            page_data["titles"].append(tag.get_text(strip=True))

        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                page_data["paragraphs"].append(text)

        # IMAGES (with copyright filtering)
        for img in soup.find_all("img"):
            src = img.get("src")
            alt = img.get("alt", "").lower()
            
            if src:
                full_url = urljoin(url, src)
                
                # Rule 1: Skip if URL or Alt text contains copyright signals
                if any(keyword in full_url.lower() or keyword in alt for keyword in COPYRIGHT_KEYWORDS):
                    print(f"[SKIP-HEURISTIC] Skipping suspected copyrighted image: {full_url}")
                    continue
                
                # Rule 2: Check for schema.org properties or rel="license" parents
                parent_with_license = img.find_parent(attrs={"rel": "license"}) or img.find_parent(attrs={"itemprop": "license"})
                if parent_with_license:
                    print(f"[SKIP-HEURISTIC] Skipping image with explicit license link: {full_url}")
                    continue
                
                page_data["images"].append(full_url)

        # VIDEOS (YouTube / iframe)
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src")
            if src:
                page_data["videos"].append(src)

        return page_data

    except Exception as e:
        print("Error:", e)
        return None


# ======================
# CRAWLER (MULTI PAGE)
# ======================
def crawl(url):
    queue = [url]

    while queue and len(visited) < MAX_PAGES:
        current_url = queue.pop(0)

        if current_url in visited:
            continue

        print(f"[CRAWLING] {current_url}")
        visited.add(current_url)

        page_data = scrape_page(current_url)

        if page_data:
            data.append(page_data)

        # find links
        try:
            res = requests.get(current_url, headers=HEADERS)
            soup = BeautifulSoup(res.text, "html.parser")

            for link in soup.find_all("a"):
                href = link.get("href")

                if href:
                    full_url = urljoin(current_url, href)

                    if is_same_domain(START_URL, full_url):
                        if full_url not in visited:
                            queue.append(full_url)

            time.sleep(1)  # avoid blocking

        except:
            continue


# ======================
# SAVE OUTPUT & DOWNLOAD
# ======================
def download_assets(domain):
    assets_dir = f"{domain}_assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"[INFO] Created folder: {assets_dir}")

    downloaded_urls = set()

    for page in data:
        urls_to_download = []
        if "images" in page:
            urls_to_download.extend(page["images"])
        if "videos" in page:
            urls_to_download.extend(page["videos"])

        for url in urls_to_download:
            if url in downloaded_urls:
                continue

            if not url.startswith(("http://", "https://")):
                continue

            try:
                print(f"[DOWNLOADING] {url}")
                # We fetch the entire content directly to inspect it
                response = requests.get(url, headers=HEADERS, timeout=15)
                if response.status_code != 200:
                    print(f"[WARNING] Failed to download {url}: HTTP status {response.status_code}")
                    continue

                parsed = urlparse(url)
                path = parsed.path
                base_name = os.path.basename(path)
                base_name = re.sub(r'[\\/*?:"<>|]', "", base_name)

                root, ext = os.path.splitext(base_name)

                # Guess extension if missing
                content_type = response.headers.get("content-type", "")
                mime_type = content_type.split(";")[0].strip()
                if not ext:
                    guess_ext = mimetypes.guess_extension(mime_type)
                    if guess_ext:
                        ext = guess_ext
                    else:
                        if "image" in mime_type:
                            ext = ".jpg"
                        elif "video" in mime_type:
                            ext = ".mp4"

                if not root:
                    hash_val = hashlib.md5(url.encode('utf-8')).hexdigest()
                    root = f"asset_{hash_val}"

                # Rule 3: Post-download metadata check (EXIF check for images)
                if "image" in mime_type or ext in [".jpg", ".jpeg", ".png", ".tiff"]:
                    try:
                        from PIL import Image
                        from PIL.ExifTags import TAGS
                        
                        img = Image.open(io.BytesIO(response.content))
                        exif_data = img.getexif()
                        is_copyrighted = False
                        
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == "Copyright" or "copyright" in str(value).lower():
                                is_copyrighted = True
                                break
                        
                        if is_copyrighted:
                            print(f"[SKIP-EXIF] Skipping image because EXIF metadata contains copyright: {url}")
                            continue
                    except ImportError:
                        # Pillow is not installed, fallback to saving
                        pass
                    except Exception as exif_err:
                        # Failed to parse EXIF (not supported format or corrupted)
                        pass

                base_name = f"{root}{ext}"
                dest_path = os.path.join(assets_dir, base_name)

                # Avoid collision with existing files
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(assets_dir, f"{root}_{counter}{ext}")
                    counter += 1

                with open(dest_path, "wb") as f:
                    f.write(response.content)
                
                print(f"[SAVED] {url} -> {dest_path}")
                downloaded_urls.add(url)
            except Exception as e:
                print(f"[ERROR] Error downloading {url}: {e}")


def save():
    domain = urlparse(START_URL).netloc.replace(".", "_")

    filename = f"{domain}.json"

    df = pd.DataFrame(data)
    df.to_json(filename, orient="records", indent=2)

    print(f"[DONE] Saved to {filename}")
    
    print("[INFO] Starting download of assets...")
    download_assets(domain)


# ======================
# RUN
# ======================
if __name__ == "__main__":
    print("===== SAFE FULL WEBSITE CRAWLER STARTED =====")
    crawl(START_URL)
    save()
    print("===== COMPLETE =====")


