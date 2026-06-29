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
        """Fetch news from Google News RSS feed (highly reliable, no key needed)."""
        logger.info("Fetching news from Google News RSS...")
        articles = []
        try:
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            for entry in feed.entries[:25]:
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
                    "source_name": source_name,
                    "popularity_score": 50.0,  # Base popularity
                    "language": "en",
                    "country": "US"
                })
        except Exception as e:
            logger.error(f"Error fetching Google News RSS: {str(e)}")
        return articles

    def fetch_reddit_news(self) -> list:
        """Fetch trending news from Reddit (/r/news and /r/worldnews) using JSON endpoint."""
        logger.info("Fetching news from Reddit /r/news and /r/worldnews...")
        articles = []
        subreddits = ["news", "worldnews"]
        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post = child.get("data", {})
                        if post.get("is_self"):
                            continue  # Skip text posts, focus on link posts
                        
                        # Popularity score based on ups (upvotes) and num_comments
                        ups = post.get("ups", 0)
                        comments = post.get("num_comments", 0)
                        popularity = min(100.0, (ups * 0.05) + (comments * 0.1))
                        
                        created_utc = post.get("created_utc")
                        published_at = datetime.utcfromtimestamp(created_utc) if created_utc else datetime.utcnow()
                        
                        articles.append({
                            "title": post.get("title"),
                            "description": f"Reddit post on r/{sub} with {ups} upvotes and {comments} comments.",
                            "full_content": post.get("title"),
                            "source_url": post.get("url"),
                            "image_url": post.get("thumbnail") if post.get("thumbnail", "").startswith("http") else None,
                            "author": post.get("author"),
                            "published_at": published_at,
                            "category": "General",
                            "source_name": f"Reddit r/{sub}",
                            "popularity_score": popularity,
                            "language": "en",
                            "country": "US"
                        })
                else:
                    logger.warning(f"Reddit API returned status {response.status_code} for r/{sub}")
            except Exception as e:
                logger.error(f"Error fetching Reddit news from r/{sub}: {str(e)}")
        return articles

    def fetch_rss_feeds(self) -> list:
        """Fetch high-quality global news RSS feeds."""
        logger.info("Fetching standard RSS feeds...")
        feeds = {
            "BBC World News": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "BBC Tech News": "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "NYT Home Page": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "CNN Top Stories": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "TechCrunch": "https://techcrunch.com/feed/",
            "Wired News": "https://www.wired.com/feed/rss",
            "The Verge": "https://www.theverge.com/rss/index.xml"
        }
        articles = []
        for source, url in feeds.items():
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:15]:
                    published_at = datetime.utcnow()
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    
                    articles.append({
                        "title": entry.title,
                        "description": entry.summary if hasattr(entry, "summary") else "",
                        "full_content": entry.summary if hasattr(entry, "summary") else "",
                        "source_url": entry.link,
                        "image_url": entry.media_content[0]["url"] if hasattr(entry, "media_content") and entry.media_content else None,
                        "author": source,
                        "published_at": published_at,
                        "category": "World",
                        "source_name": source,
                        "popularity_score": 60.0,
                        "language": "en",
                        "country": "US"
                    })
            except Exception as e:
                logger.error(f"Error parsing RSS feed for {source}: {str(e)}")
        return articles

    def fetch_news_api(self) -> list:
        """Fetch news from News API if api key is configured."""
        if not settings.NEWS_API_KEY:
            return []
        
        logger.info("Fetching from News API...")
        articles = []
        try:
            url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={settings.NEWS_API_KEY}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("articles", [])[:20]:
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
                        "source_name": item.get("source", {}).get("name") or "NewsAPI",
                        "popularity_score": 75.0,  # Highly curated trending topics
                        "language": "en",
                        "country": "US"
                    })
        except Exception as e:
            logger.error(f"Error fetching from News API: {str(e)}")
        return articles

    def fetch_currents_news(self) -> list:
        """Fetch news from Currents API if api key is configured."""
        if not settings.CURRENTS_API_KEY:
            return []
        
        logger.info("Fetching from Currents API...")
        articles = []
        try:
            url = "https://api.currentsapi.services/v1/latest-news"
            headers = {"Authorization": f"{settings.CURRENTS_API_KEY}"}  # Direct key is standard or Bearer. Let's do Bearer to be safe
            if not settings.CURRENTS_API_KEY.startswith("Bearer "):
                headers = {"Authorization": f"Bearer {settings.CURRENTS_API_KEY}"}
            
            params = {
                "language": "en"
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("news", [])[:20]:
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
                        "source_name": "CurrentsAPI",
                        "popularity_score": 70.0,
                        "language": item.get("language") or "en",
                        "country": "US"
                    })
            else:
                logger.warning(f"Currents API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching from Currents API: {str(e)}")
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
