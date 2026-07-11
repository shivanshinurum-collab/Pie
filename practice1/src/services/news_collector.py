import hashlib
import urllib.parse
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
import feedparser
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from src.config import settings, logger
from src.database import NewsArticle

class NewsCollectorService:
    def __init__(self, db: Session):
        self.db = db
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def compute_hash(self, title: str, url: str) -> str:
        """Compute SHA256 hash to prevent duplicate news entries."""
        combined = f"{title.strip().lower()}:{url.strip().lower()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def is_valid_news_title(self, title: str) -> bool:
        """Filter out low-quality/junk/promotional articles."""
        if not title or len(title.strip()) < 15:
            return False
            
        # Common patterns for live-blogs, shopping guides, promos, crosswords, etc.
        junk_patterns = [
            r"\b(live updates|live coverage|live blog|live)\b",
            r"\b(deals of the day|best deals|coupon|promo code|how to watch|where to watch)\b",
            r"\b(crossword|sudoku|daily quiz|horoscope|weather forecast)\b",
            r"\b(obituary|obituaries|dies at)\b",
            r"\b(newsletter|subscribe|deals|shopping|buying guide|gift guide)\b"
        ]
        
        title_lower = title.lower()
        for pattern in junk_patterns:
            if re.search(pattern, title_lower):
                return False
                
        return True

    def fetch_google_news_rss(self) -> list:
        """Fetch news from Google News RSS feed (80% India, 20% US)."""
        logger.info("Fetching news from Google News RSS...")
        articles = []
        
        # Configure the sources: (url, limit, country_code)
        sources = [
            ("https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en", 20, "IN"),
            ("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", 5, "US")
        ]
        
        for url, limit, country in sources:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:limit]:
                    # Google News RSS titles are formatted as "Headline - Source"
                    title = entry.title
                    source_name = "Google News"
                    if " - " in title:
                        parts = title.split(" - ")
                        title = " - ".join(parts[:-1])
                        source_name = parts[-1]
                    
                    published_at = datetime.utcnow()
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    
                    articles.append({
                        "title": title,
                        "description": entry.summary if hasattr(entry, "summary") else "",
                        "full_content": entry.summary if hasattr(entry, "summary") else "",
                        "source_url": entry.link,
                        "image_url": None,
                        "author": "Google News",
                        "published_at": published_at,
                        "category": "General",
                        "source_name": f"{source_name} ({country})",
                        "popularity_score": 50.0,  # Base popularity
                        "language": "en",
                        "country": country
                    })
            except Exception as e:
                logger.error(f"Error fetching Google News RSS ({country}): {str(e)}")
        return articles

    def fetch_reddit_news(self) -> list:
        """Fetch trending news from Reddit (80% r/india, 20% r/worldnews)."""
        logger.info("Fetching news from Reddit /r/india and /r/worldnews...")
        articles = []
        
        # Configure subreddits: (name, limit, country)
        subreddits = [
            ("india", 12, "IN"),
            ("worldnews", 3, "World")
        ]
        
        for sub, limit, country in subreddits:
            try:
                # We use .rss because Reddit blocks public unauthenticated JSON API endpoints (403 Forbidden).
                url = f"https://www.reddit.com/r/{sub}/.rss"
                
                # Retry logic for 429 rate limiting
                max_retries = 3
                retry_delay = 3
                response = None
                for attempt in range(max_retries):
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:
                        logger.warning(f"Reddit RSS rate-limited (429) for r/{sub}, retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        break
                
                if response and response.status_code == 200:
                    parsed = feedparser.parse(response.text)
                    for entry in parsed.entries[:limit]:
                        # Extract author username safely
                        author = entry.get("author", "Unknown")
                        if author.startswith("/u/"):
                            author = author[3:]
                        
                        # Extract the actual external news article URL from the description/content HTML
                        content_val = entry.content[0].value if hasattr(entry, "content") and entry.content else (entry.summary if hasattr(entry, "summary") else "")
                        links = re.findall(r'href="([^"]+)"', content_val)
                        source_url = entry.link
                        is_self = True
                        for l in links:
                            if "reddit.com" not in l and not l.startswith("/"):
                                source_url = l
                                is_self = False
                                break
                        
                        if is_self:
                            continue  # Skip text posts, focus on link posts
                        
                        # Use updated or published parsed date
                        published_at = datetime.utcnow()
                        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                            published_at = datetime(*entry.updated_parsed[:6])
                        elif hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6])
                        
                        # High popularity since it is trending in top subreddits hot feed
                        popularity = 80.0
                        
                        articles.append({
                            "title": entry.title,
                            "description": f"Reddit post on r/{sub} by /u/{author}.",
                            "full_content": entry.title,
                            "source_url": source_url,
                            "image_url": None,
                            "author": author,
                            "published_at": published_at,
                            "category": "General",
                            "source_name": f"Reddit r/{sub}",
                            "popularity_score": popularity,
                            "language": "en",
                            "country": country
                        })
                else:
                    status_code = response.status_code if response else "No Response"
                    logger.warning(f"Reddit RSS failed with status {status_code} for r/{sub}")
            except Exception as e:
                logger.error(f"Error fetching Reddit news from r/{sub}: {str(e)}")
            
            # Add a small delay between subreddits to prevent IP-based rate limiting
            import time
            time.sleep(2)
            
        return articles

    def fetch_rss_feeds(self) -> list:
        """Fetch high-quality news RSS feeds (80% India, 20% Global)."""
        logger.info("Fetching standard RSS feeds...")
        
        # Configure feeds: (source_name, url, limit, country)
        feeds = [
            # Indian feeds (limit: 15 each)
            ("Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", 15, "IN"),
            ("The Hindu", "https://www.thehindu.com/news/national/feeder/default.xml", 15, "IN"),
            ("Indian Express", "https://indianexpress.com/feed/", 15, "IN"),
            ("NDTV News", "https://feeds.feedburner.com/ndtvnews-top-stories", 15, "IN"),
            
            # Global feeds (limit: 3 each)
            ("BBC World News", "http://feeds.bbci.co.uk/news/world/rss.xml", 3, "World"),
            ("TechCrunch", "https://techcrunch.com/feed/", 3, "World"),
            ("Wired News", "https://www.wired.com/feed/rss", 3, "World")
        ]
        
        articles = []
        for source, url, limit, country in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:limit]:
                    published_at = datetime.utcnow()
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    
                    articles.append({
                        "title": entry.title,
                        "description": entry.summary if hasattr(entry, "summary") else "",
                        "full_content": entry.summary if hasattr(entry, "summary") else "",
                        "source_url": entry.link,
                        "image_url": entry.media_content[0].get("url") if hasattr(entry, "media_content") and entry.media_content and isinstance(entry.media_content[0], dict) else None,
                        "author": source,
                        "published_at": published_at,
                        "category": "National" if country == "IN" else "World",
                        "source_name": source,
                        "popularity_score": 60.0,
                        "language": "en",
                        "country": country
                    })
            except Exception as e:
                logger.error(f"Error parsing RSS feed for {source}: {str(e)}")
        return articles

    def fetch_news_api(self) -> list:
        """Fetch news from News API if api key is configured (80% India, 20% Global)."""
        if not settings.NEWS_API_KEY:
            return []
        
        logger.info("Fetching from News API...")
        articles = []
        
        # Configure targets: (params_string, limit, country)
        targets = [
            ("country=in", 16, "IN"),
            ("language=en", 4, "World")
        ]
        
        for params_str, limit, country in targets:
            try:
                url = f"https://newsapi.org/v2/top-headlines?{params_str}&apiKey={settings.NEWS_API_KEY}"
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("articles", [])[:limit]:
                        pub_str = item.get("publishedAt")
                        published_at = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ") if pub_str else datetime.utcnow()
                        
                        articles.append({
                            "title": item.get("title"),
                            "description": item.get("description") or "",
                            "full_content": item.get("content") or item.get("description") or "",
                            "source_url": item.get("url"),
                            "image_url": item.get("urlToImage"),
                            "author": item.get("author") or "NewsAPI",
                            "published_at": published_at,
                            "category": "General",
                            "source_name": f"{item.get('source', {}).get('name') or 'NewsAPI'} ({country})",
                            "popularity_score": 75.0,  # Highly curated trending topics
                            "language": "en",
                            "country": country
                        })
            except Exception as e:
                logger.error(f"Error fetching from News API ({country}): {str(e)}")
        return articles

    def fetch_currents_news(self) -> list:
        """Fetch news from Currents API if api key is configured (80% India, 20% Global)."""
        if not settings.CURRENTS_API_KEY:
            return []
        
        logger.info("Fetching from Currents API...")
        articles = []
        
        # Configure targets: (extra_params_dict, limit, country)
        targets = [
            ({"country": "IN", "language": "en"}, 16, "IN"),
            ({"language": "en"}, 4, "World")
        ]
        
        url = "https://api.currentsapi.services/v1/latest-news"
        headers = {"Authorization": f"{settings.CURRENTS_API_KEY}"}
        if not settings.CURRENTS_API_KEY.startswith("Bearer "):
            headers = {"Authorization": f"Bearer {settings.CURRENTS_API_KEY}"}
            
        for extra_params, limit, country in targets:
            try:
                response = requests.get(url, headers=headers, params=extra_params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("news", [])[:limit]:
                        pub_str = item.get("published")
                        if pub_str and len(pub_str) >= 19:
                            try:
                                published_at = datetime.strptime(pub_str[:19], "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                published_at = datetime.utcnow()
                        else:
                            published_at = datetime.utcnow()
                        
                        categories = item.get("category", [])
                        category = categories[0].capitalize() if categories else "General"
                        
                        articles.append({
                            "title": item.get("title"),
                            "description": item.get("description") or "",
                            "full_content": item.get("description") or "",
                            "source_url": item.get("url"),
                            "image_url": item.get("image"),
                            "author": item.get("author") or "CurrentsAPI",
                            "published_at": published_at,
                            "category": category,
                            "source_name": f"CurrentsAPI ({country})",
                            "popularity_score": 70.0,
                            "language": item.get("language") or "en",
                            "country": country
                        })
                else:
                    logger.warning(f"Currents API returned status {response.status_code} for {country}: {response.text}")
            except Exception as e:
                logger.error(f"Error fetching from Currents API ({country}): {str(e)}")
        return articles

    def scrape_full_article_content(self, url: str) -> str:
        """Scrape full body content from article URL to enrich the context."""
        try:
            response = requests.get(url, headers=self.headers, timeout=8)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "header", "footer"]):
                    script.extract()
                
                # Fetch text from paragraphs
                paragraphs = soup.find_all("p")
                text_content = " ".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30])
                return text_content[:4000]  # Limit length for LLM context compatibility
        except Exception as e:
            logger.debug(f"Could not scrape full article content from {url}: {str(e)}")
        return ""

    def collect_and_save(self) -> int:
        """Run all collectors, deduplicate, score, and persist new articles."""
        all_fetched = []
        
        # Run scraping modules
        all_fetched.extend(self.fetch_google_news_rss())
        all_fetched.extend(self.fetch_reddit_news())
        all_fetched.extend(self.fetch_rss_feeds())
        all_fetched.extend(self.fetch_news_api())
        all_fetched.extend(self.fetch_currents_news())
        
        logger.info(f"Total raw news items collected: {len(all_fetched)}")
        
        new_count = 0
        for data in all_fetched:
            if not data["title"] or not data["source_url"]:
                continue
            if not self.is_valid_news_title(data["title"]):
                logger.debug(f"Filtering out low-quality/junk article title: {data['title']}")
                continue
            
            content_hash = self.compute_hash(data["title"], data["source_url"])
            
            # Check for duplicates in DB
            exists = self.db.query(NewsArticle).filter(NewsArticle.content_hash == content_hash).first()
            if not exists:
                # Scrape full article content to provide high-quality LLM prompts
                logger.debug(f"Scraping full content for new article: {data['title'][:50]}")
                full_body = self.scrape_full_article_content(data["source_url"])
                if full_body:
                    data["full_content"] = full_body
                
                article = NewsArticle(
                    title=data["title"],
                    description=data["description"],
                    full_content=data["full_content"],
                    source_url=data["source_url"],
                    image_url=data["image_url"],
                    author=data["author"],
                    published_at=data["published_at"],
                    category=data["category"],
                    source_name=data["source_name"],
                    popularity_score=data["popularity_score"],
                    language=data["language"],
                    country=data["country"],
                    content_hash=content_hash,
                    processing_status="pending"
                )
                self.db.add(article)
                new_count += 1
        
        if new_count > 0:
            self.db.commit()
            logger.info(f"Successfully added {new_count} new unique news articles to the database.")
        else:
            logger.info("No new unique articles found.")
            
        return new_count
