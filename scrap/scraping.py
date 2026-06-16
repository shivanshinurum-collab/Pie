import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time
import os
import hashlib
import re
import mimetypes


# ======================
# CONFIG
# ======================
START_URL = "https://www.flipkart.com/"
MAX_PAGES = 20   # safety limit (change if needed)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

visited = set()
data = []


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

        # IMAGES
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                page_data["images"].append(urljoin(url, src))

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
# SAVE OUTPUT
# ======================
# def save():
#     df = pd.DataFrame(data)
#     df.to_json(f"{START_URL}.json", indent=2)
#     print(f"[DONE] Saved to {START_URL}.json")


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
                response = requests.get(url, headers=HEADERS, timeout=15, stream=True)
                if response.status_code != 200:
                    print(f"[WARNING] Failed to download {url}: HTTP status {response.status_code}")
                    continue

                parsed = urlparse(url)
                path = parsed.path
                base_name = os.path.basename(path)
                base_name = re.sub(r'[\\/*?:"<>|]', "", base_name)

                root, ext = os.path.splitext(base_name)

                # Guess extension if missing
                if not ext:
                    content_type = response.headers.get("content-type", "")
                    mime_type = content_type.split(";")[0].strip()
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

                base_name = f"{root}{ext}"
                dest_path = os.path.join(assets_dir, base_name)

                # Avoid collision with existing files
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(assets_dir, f"{root}_{counter}{ext}")
                    counter += 1

                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
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
    print("===== FULL WEBSITE CRAWLER STARTED =====")
    crawl(START_URL)
    save()
    print("===== COMPLETE =====")







