import json
import os
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from src.config import settings, logger
from src.database import NewsArticle, Meme

# Pydantic schema representing the LLM output structure for news analysis
class NewsAnalysisResult(BaseModel):
    topic: str = Field(description="The primary high-level topic or domain of the article.")
    entities: list[str] = Field(description="Key names, organizations, or products mentioned in the article.")
    people: list[str] = Field(description="Celebrities, politicians, or notable figures mentioned.")
    country: str = Field(description="Country context of the news.")
    sentiment: str = Field(description="Overall sentiment: Positive, Negative, Neutral, or Chaos.")
    emotion: str = Field(description="Dominant emotion invoked: Outrage, Surprise, Humor, Hope, Fear, Sarcasm.")
    funny_potential: str = Field(description="Detailed reason explaining why this news has humor or meme potential.")
    meme_potential_score: int = Field(description="Score between 0 (not funny) and 100 (meme goldmine).", ge=0, le=100)
    instagram_potential_score: int = Field(description="Score between 0 (boring) and 100 (highly shareable on IG).", ge=0, le=100)
    one_line_summary: str = Field(description="A catchy, concise one-line summary of the news.")
    news_context: str = Field(description="Historical context or background explanation for why this is interesting or controversial.")
    can_become_meme: bool = Field(description="Whether this story can easily translate to a viral graphic meme.")

class NewsAnalystService:
    def __init__(self, db: Session):
        self.db = db
        self.system_prompt = (
            "You are a Senior Meme Architect, Pop Culture Historian, and Viral Social Media Specialist.\n"
            "Your task is to analyze breaking news articles and evaluate their potential to become viral memes.\n"
            "Evaluate objectively. Focus on absurdity, hypocrisy, irony, massive public interest, or relatable scenarios.\n"
            "You MUST return a JSON object adhering exactly to the requested schema layout."
        )

    def _query_gemini(self, prompt: str) -> str:
        """Call Gemini 2.5 Flash / Gemini 1.5 Pro to analyze the news."""
        import google.generativeai as genai
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        # Use gemini-1.5-flash as the standard fast and smart model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=self.system_prompt
        )
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text

    def _query_openai(self, prompt: str) -> str:
        """Call OpenAI GPT-4o-mini to analyze the news."""
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def _query_claude(self, prompt: str) -> str:
        """Call Anthropic Claude 3.5 Sonnet to analyze the news."""
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": f"{prompt}\nReturn JSON only."}
            ]
        )
        return response.content[0].text

    def _query_ollama(self, prompt: str) -> str:
        """Call local Ollama to analyze the news."""
        import requests
        url = f"{settings.OLLAMA_URL}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "")
        else:
            raise Exception(f"Ollama API returned status {response.status_code}: {response.text}")

    def analyze_article(self, article: NewsArticle) -> NewsAnalysisResult:
        """Analyze a single article using available LLM API keys with auto-fallback."""
        prompt = (
            f"Analyze the following breaking news article:\n"
            f"Title: {article.title}\n"
            f"Source: {article.source_name}\n"
            f"Description: {article.description}\n"
            f"Full Content: {article.full_content}\n\n"
            f"Provide an analysis mapping to this JSON structure:\n"
            "{\n"
            '  "topic": "Domain (e.g., Tech, Sports, Politics)",\n'
            '  "entities": ["list", "of", "entities"],\n'
            '  "people": ["list", "of", "people"],\n'
            '  "country": "Country Context",\n'
            '  "sentiment": "Positive | Negative | Neutral | Chaos",\n'
            '  "emotion": "Outrage | Surprise | Humor | Hope | Fear | Sarcasm",\n'
            '  "funny_potential": "Why is this news funny or memeable?",\n'
            '  "meme_potential_score": 0-100,\n'
            '  "instagram_potential_score": 0-100,\n'
            '  "one_line_summary": "Catchy headline",\n'
            '  "news_context": "Background context details",\n'
            '  "can_become_meme": true | false\n'
            "}"
        )
        
        raw_response = None
        
        # 1. Try Gemini first
        if settings.GOOGLE_API_KEY:
            try:
                logger.info(f"Analyzing article with Gemini: {article.title[:50]}")
                raw_response = self._query_gemini(prompt)
            except Exception as e:
                logger.error(f"Gemini analysis failed: {str(e)}")
        
        # 2. Fallback to OpenAI
        if not raw_response and settings.OPENAI_API_KEY:
            try:
                logger.info(f"Analyzing article with OpenAI: {article.title[:50]}")
                raw_response = self._query_openai(prompt)
            except Exception as e:
                logger.error(f"OpenAI analysis failed: {str(e)}")
                
        # 3. Fallback to Claude
        if not raw_response and settings.ANTHROPIC_API_KEY:
            try:
                logger.info(f"Analyzing article with Claude: {article.title[:50]}")
                raw_response = self._query_claude(prompt)
            except Exception as e:
                logger.error(f"Claude analysis failed: {str(e)}")

        # 4. Try local Ollama if no cloud keys are active
        if not raw_response:
            try:
                logger.info(f"Analyzing article with Ollama '{settings.OLLAMA_MODEL}': {article.title[:50]}")
                raw_response = self._query_ollama(prompt)
            except Exception as e:
                logger.error(f"Ollama analysis failed: {str(e)}")

        # 5. Mock Local Fallback (if no keys and Ollama fails)
        if not raw_response:
            logger.warning("No LLM API keys provided and Ollama failed! Generating mock analysis.")
            raw_response = json.dumps({
                "topic": "World News",
                "entities": [article.source_name or "Unknown"],
                "people": [],
                "country": article.country or "Global",
                "sentiment": "Chaos",
                "emotion": "Surprise",
                "funny_potential": f"Based on the real news about '{article.title}', this has huge viral meme potential.",
                "meme_potential_score": 85,
                "instagram_potential_score": 80,
                "one_line_summary": article.title[:100],
                "news_context": article.description or "No content available.",
                "can_become_meme": True
            })

        # Parse and validate the response
        try:
            # Strip markdown block formatting if present in the LLM response
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            data = json.loads(cleaned_response)
            return NewsAnalysisResult(**data)
        except Exception as e:
            logger.error(f"Error parsing LLM response as NewsAnalysisResult: {str(e)}. Raw: {raw_response}")
            # Safe basic schema mapping on JSON decoding failures
            return NewsAnalysisResult(
                topic="General",
                entities=[],
                people=[],
                country="US",
                sentiment="Neutral",
                emotion="Surprise",
                funny_potential="Failed to parse LLM structured json.",
                meme_potential_score=20,
                instagram_potential_score=20,
                one_line_summary=article.title[:80],
                news_context=article.description or "",
                can_become_meme=False
            )

    def process_pending_articles(self) -> int:
        """Query and analyze all pending articles in the database."""
        pending_articles = self.db.query(NewsArticle).filter(
            NewsArticle.processing_status == "pending"
        ).order_by(NewsArticle.popularity_score.desc()).all()
        
        logger.info(f"Found {len(pending_articles)} pending articles for AI analysis.")
        
        analyzed_count = 0
        for article in pending_articles:
            try:
                analysis = self.analyze_article(article)
                
                # Check threshold for generating memes
                if analysis.can_become_meme and analysis.meme_potential_score >= settings.MEME_POTENTIAL_THRESHOLD:
                    # Create meme entry in database
                    meme = Meme(
                        news_article_id=article.id,
                        topic=analysis.topic,
                        primary_sentiment=analysis.sentiment,
                        meme_potential_score=analysis.meme_potential_score,
                        instagram_potential_score=analysis.instagram_potential_score,
                        one_line_summary=analysis.one_line_summary,
                        news_context=analysis.news_context,
                        meme_status="pending"
                    )
                    self.db.add(meme)
                    article.processing_status = "analyzed"
                    logger.info(f"Article '{article.title[:40]}' met threshold. Queued for Meme Generation.")
                else:
                    article.processing_status = "skipped"
                    logger.info(f"Article '{article.title[:40]}' skipped (Meme Potential Score: {analysis.meme_potential_score}).")
                
                analyzed_count += 1
            except Exception as e:
                logger.error(f"Failed to analyze article {article.id}: {str(e)}")
                article.processing_status = "failed"
                
        self.db.commit()
        return analyzed_count
