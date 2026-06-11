import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time


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


def save():
    domain = urlparse(START_URL).netloc.replace(".", "_")

    filename = f"{domain}.json"

    df = pd.DataFrame(data)
    df.to_json(filename, orient="records", indent=2)

    print(f"[DONE] Saved to {filename}")


# ======================
# RUN
# ======================
if __name__ == "__main__":
    print("===== FULL WEBSITE CRAWLER STARTED =====")
    crawl(START_URL)
    save()
    print("===== COMPLETE =====")


##### 1st

# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import time


# # =========================
# # CONFIG
# # =========================
# URL = "https://inurum.com/"   # change this
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# }


# # =========================
# # STATIC SCRAPER
# # =========================
# def scrape_static(url):
#     print("[INFO] Trying static scraping...")

#     try:
#         response = requests.get(url, headers=HEADERS, timeout=10)

#         if response.status_code != 200:
#             print("Failed with status:", response.status_code)
#             return None

#         soup = BeautifulSoup(response.text, "lxml")

#         data = []

#         # ---- BASIC EXAMPLES (EDIT AS NEEDED) ----
#         titles = soup.find_all(["h1", "h2", "h3"])
#         paragraphs = soup.find_all("p")

#         for t in titles:
#             data.append({"type": "title", "text": t.get_text(strip=True)})

#         for p in paragraphs:
#             text = p.get_text(strip=True)
#             if len(text) > 0:
#                 data.append({"type": "paragraph", "text": text})

#         return data

#     except Exception as e:
#         print("Static scraping error:", e)
#         return None


# # =========================
# # SAVE DATA
# # =========================
# def save_data(data, filename="output.csv"):
#     df = pd.DataFrame(data)
#     df.to_csv(filename, index=False)
#     print(f"[SUCCESS] Data saved to {filename}")


# # =========================
# # MAIN FUNCTION
# # =========================
# def main():
#     print("===== WEB SCRAPER STARTED =====")

#     data = scrape_static(URL)

#     if data:
#         save_data(data)
#     else:
#         print("[INFO] No static data found. Consider Selenium for JS sites.")

#     print("===== DONE =====")


# if __name__ == "__main__":
#     main()