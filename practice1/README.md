# AI News Meme Engine - Execution Guide

This guide explains how to configure and run the Autonomous AI News Meme Engine.

## 1. Setup Environment Variables

Create a file named `.env` at the root of the project (`/Users/shubhamjain/Documents/pai/practice1/.env`) and add your credentials:

```env
# --- General Environment Configurations ---
ENV=production
DEBUG=True
STORAGE_TYPE=local

# --- Database & Redis URL (Defaults for Docker Compose) ---
DATABASE_URL=postgresql://postgres:postgres@db:5432/news_meme_db
REDIS_URL=redis://redis:6379/0

# --- LLM API Keys (Gemini is recommended and used as the default) ---
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key

# --- Image Generation APIs ---
REPLICATE_API_KEY=your_replicate_api_key_for_flux

# --- Scraping Keys (Optional, RSS and Reddit work without keys) ---
NEWS_API_KEY=your_newsapi_org_key

# --- Instagram API (Optional, falls back to mock simulation files if blank) ---
INSTAGRAM_ACCESS_TOKEN=your_fb_page_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id
```

---

## 2. Option A: Run Using Docker Compose (Recommended)

Docker Compose automatically spins up the application, database, broker, and all scheduler workers in isolated containers.

### Start the entire stack
Run this command from the root of the workspace:
```bash
docker compose -f docker/docker-compose.yml up --build -d
```

This will launch:
1. **FastAPI Web Server** at `http://localhost:8000`
2. **Postgres Database** at port `5432`
3. **Redis Task Broker** at port `6379`
4. **Celery Worker** (Handles tasks)
5. **Celery Beat** (Periodic scheduler triggers news sweeps every 15 mins)

### View Logs
```bash
docker compose -f docker/docker-compose.yml logs -f
```

### Stop Stack
```bash
docker compose -f docker/docker-compose.yml down
```

---

## 3. Option B: Run Locally Using Virtual Environment

If you prefer to run services manually on your local system without Docker:

### Step 1: Activate Virtual Environment
```bash
source /Users/shubhamjain/Documents/pai/.venv/bin/activate
```

### Step 2: Set Local Environment variables
Edit `.env` to point database and redis to localhost:
```env
DATABASE_URL=sqlite:///news_meme_db.db
REDIS_URL=redis://localhost:6379/0
```

### Step 3: Run FastAPI App
```bash
uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```

### Step 4: Run Celery Worker (In a separate terminal)
Make sure Redis server is running locally:
```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

### Step 5: Run Celery Beat Scheduler (In a separate terminal)
```bash
celery -A src.tasks.celery_app beat --loglevel=info
```

---

## 4. API Endpoints Dashboard

Once the app is running (via Docker or local), open `http://localhost:8000` in your browser. You can use the Swagger UI at `http://localhost:8000/docs` to:

- `POST /api/v1/trigger/collect`: Trigger a news scrape sweep manually.
- `GET /api/v1/news`: Inspect collected news articles.
- `GET /api/v1/memes`: View generated memes and details (composed image static link, voiceover script, captions).
- `GET /api/v1/publications`: View publication outcomes.
