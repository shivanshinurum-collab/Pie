import json
from pydantic import BaseModel, Field
from src.config import settings, logger

# Pydantic schemas representing structured output
class MemeVariationText(BaseModel):
    funny: str = Field(description="Funny/relatable reaction caption for the bottom of the meme image.")
    savage: str = Field(description="Savage/roast style reaction caption.")
    dark: str = Field(description="Slightly dark/gallows humor reaction caption (brand-safe, non-offensive).")
    wholesome: str = Field(description="Heartwarming or positive spin reaction caption.")
    sarcastic: str = Field(description="Heavy sarcasm or ironic reaction caption.")

class HumorCaption(BaseModel):
    style: str = Field(description="Indian, Global, Gen Z, Dark, Sports, or Political neutral")
    length: str = Field(description="short | long")
    text: str = Field(description="The meme caption content.")

class InstagramPackage(BaseModel):
    post_caption: str = Field(description="The primary engaging copy for the Instagram caption.")
    hook: str = Field(description="A highly engaging first line (hook) to catch scrolling users.")
    cta: str = Field(description="Call to action (e.g. comment below, tag a friend, share).")
    hashtags: list[str] = Field(description="10-15 trending and niche-specific hashtags.")
    seo_keywords: list[str] = Field(description="SEO keywords to boost post discovery.")

class CaptionGenerationResult(BaseModel):
    variations: MemeVariationText
    captions: list[HumorCaption]
    instagram: InstagramPackage

class CaptionGeneratorService:
    def __init__(self):
        self.system_prompt = (
            "You are a World-Class Copywriter, Viral Content Creator, and Internet Culture Specialist.\n"
            "You write highly viral captions, reaction copy, and tags for Instagram meme pages.\n"
            "Keep the humor authentic, punchy, and appropriate for general social media guidelines (no hate speech, no graphic violence, no real harm).\n"
            "You MUST return a JSON object adhering exactly to the requested schema layout."
        )

    def _query_llm(self, prompt: str, title: str = "", summary: str = "") -> str:
        """Helper to query the configured LLM (Gemini first, fallback to OpenAI)."""
        raw_response = None
        
        # 1. Gemini
        if settings.GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=self.system_prompt
                )
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                raw_response = response.text
            except Exception as e:
                logger.error(f"Gemini caption generation failed: {str(e)}")

        # 2. OpenAI
        if not raw_response and settings.OPENAI_API_KEY:
            try:
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
                raw_response = response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI caption generation failed: {str(e)}")

        # 2.5. Try local Ollama
        if not raw_response:
            try:
                logger.info(f"Generating captions with local Ollama model '{settings.OLLAMA_MODEL}'...")
                raw_response = self._query_ollama(prompt)
            except Exception as e:
                logger.error(f"Ollama caption generation failed: {str(e)}")

        # 3. Local Default Fallback (if no keys and Ollama fails)
        if not raw_response:
            logger.warning("No LLM key active and Ollama failed. Providing static mock captions.")
            # Truncate title for caption display to prevent layout clutter
            title_short = title
            if len(title_short) > 60:
                title_short = title_short[:57] + "..."
                
            mock_data = {
                "variations": {
                    "funny": f"Me pretending to understand '{title_short}' so I look smart in public.",
                    "savage": "Is this some kind of rich person joke that I'm too broke to understand?",
                    "dark": f"Oh brilliant, another thing to worry about instead of my empty bank account.",
                    "wholesome": "Me just minding my own business and hoping everyone has a nice day.",
                    "sarcastic": f"Wow, my life is completely changed after reading about '{title_short}'."
                },
                "captions": [
                    {"style": "Gen Z", "length": "short", "text": "no thoughts head empty 💀"},
                    {"style": "Indian", "length": "short", "text": "Alag hi chal raha h inka 😂"},
                    {"style": "Global", "length": "long", "text": f"This situation is wild: {summary}"}
                ],
                "instagram": {
                    "post_caption": f"This news is wild! {summary}. Let us know what you think in the comments 👇",
                    "hook": f"Breaking: {title} 🤯",
                    "cta": "Tag a friend who needs to see this!",
                    "hashtags": ["#breakingnews", "#memes", "#funnymemes", "#instagrammemes", "#viral"],
                    "seo_keywords": ["news", "memes", "funny", "current events"]
                }
            }
            raw_response = json.dumps(mock_data)
            
        return raw_response

    def _query_ollama(self, prompt: str) -> str:
        """Call local Ollama to generate meme captions."""
        import requests
        url = f"{settings.OLLAMA_URL}/api/chat"
        # Append clear, strong instructions for local model constraints
        ollama_instruction = (
            "\n\nCRITICAL INSTRUCTIONS FOR LOCAL MODEL:\n"
            "- In the 'variations' section (funny, savage, dark, wholesome, sarcastic), you MUST output a detailed, highly entertaining meme reaction text (around 20-30 words, spanning 2-3 lines) explaining a funny reaction or POV that incorporates the title and image context. This is to fill the bottom black footer space of the meme canvas beautifully.\n"
            "- Write plain text reaction captions only. Do NOT output URLs, links, image tags, or imgur links.\n"
            "- Examples of good meme text reactions: 'POV: You are trying to explain to your family why a semiconductor company decreasing its position is actually a life-changing event for your stock portfolio...', 'My last two brain cells trying to process the global macroeconomic implications of chip supply chains while I struggle to decide what to eat for lunch...'.\n"
            "- Keep it highly relatable, funny, and detailed enough to fill the visual space."
        )
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt + ollama_instruction},
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

    def generate_all_captions(self, title: str, summary: str, context: str, img_description: str = "") -> CaptionGenerationResult:
        """Generate structured reaction variants, captions, and IG metadata."""
        prompt = (
            f"Generate meme variations, 5 humor captions, and Instagram posting metadata for the following news:\n"
            f"Headline: {title}\n"
            f"Summary: {summary}\n"
            f"Background Context: {context}\n"
            f"Image Content Description: {img_description}\n\n"
            f"Requirements:\n"
            f"1. Generate 5 variations of meme reaction text (funny, savage, dark, wholesome, sarcastic).\n"
            f"2. Generate 5 distinct humor captions (mix of Gen Z, Indian, Global, Dark, Sports, and Political). Content must be safe and funny.\n"
            f"3. Generate an Instagram posting package (hook, post caption, CTA, hashtags, and discoverable SEO keywords).\n\n"
            f"Format the output exactly as this JSON schema:\n"
            "{\n"
            '  "variations": {\n'
            '    "funny": "...", "savage": "...", "dark": "...", "wholesome": "...", "sarcastic": "..."\n'
            '  },\n'
            '  "captions": [\n'
            '    {"style": "Gen Z | Indian | Global | Dark | Sports | Political", "length": "short | long", "text": "..."}\n'
            '  ],\n'
            '  "instagram": {\n'
            '    "post_caption": "...", "hook": "...", "cta": "...",\n'
            '    "hashtags": ["#tag1", "#tag2"], "seo_keywords": ["kw1", "kw2"]\n'
            '  }\n'
            "}"
        )
        
        raw_res = self._query_llm(prompt, title=title, summary=summary)
        try:
            cleaned_res = raw_res.strip()
            if cleaned_res.startswith("```json"):
                cleaned_res = cleaned_res[7:]
            if cleaned_res.endswith("```"):
                cleaned_res = cleaned_res[:-3]
            cleaned_res = cleaned_res.strip()
            
            data = json.loads(cleaned_res)
            return CaptionGenerationResult(**data)
        except Exception as e:
            logger.error(f"Error parsing Caption generation result: {str(e)}. Raw: {raw_res}")
            # Dynamic recovery matching basic types
            return CaptionGenerationResult(
                variations=MemeVariationText(
                    funny="This is crazy 😂",
                    savage="No way they did this.",
                    dark="A dark day indeed.",
                    wholesome="Wholesome news of the day.",
                    sarcastic="Oh, what a surprise."
                ),
                captions=[],
                instagram=InstagramPackage(
                    post_caption=f"Breaking: {title}",
                    hook="Wait for it... 🤯",
                    cta="Share your thoughts!",
                    hashtags=["#news", "#meme"],
                    seo_keywords=["news"]
                )
            )
