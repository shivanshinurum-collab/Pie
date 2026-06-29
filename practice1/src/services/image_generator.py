import os
import requests
from src.config import settings, logger

class ImageGeneratorService:
    def __init__(self):
        pass

    def generate_detailed_prompt(self, title: str, context: str) -> str:
        """Construct a high-quality photorealistic editorial prompt based on news data."""
        # Use an LLM or structured rules to build the detailed scene prompt
        prompt = (
            f"An editorial photorealistic news illustration representing: {title}. "
            f"Context: {context}. Photorealistic, cinematic lighting, highly detailed faces, "
            f"shot on 35mm lens, corporate style, high-end production, 4k resolution, "
            f"no watermarks, no text, no captions, realistic human anatomy."
        )
        return prompt

    def generate_image_flux(self, prompt: str, output_path: str) -> bool:
        """Generate image using FLUX.1 [schnell] or [dev] via Replicate API."""
        if not settings.REPLICATE_API_KEY:
            return False
        
        logger.info("Generating image via FLUX (Replicate)...")
        try:
            headers = {
                "Authorization": f"Token {settings.REPLICATE_API_KEY}",
                "Content-Type": "application/json"
            }
            # Replicate FLUX.1 Schnell model endpoint
            url = "https://api.replicate.com/v1/predictions"
            payload = {
                "version": "black-forest-labs/flux-schnell",
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "output_format": "jpg",
                    "disable_safety_checker": False
                }
            }
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 201:
                prediction = response.json()
                predict_id = prediction["id"]
                poll_url = f"https://api.replicate.com/v1/predictions/{predict_id}"
                
                # Poll for completion (schnell usually completes in 1-4 seconds)
                import time
                for _ in range(15):
                    poll_res = requests.get(poll_url, headers=headers, timeout=10)
                    if poll_res.status_code == 200:
                        status_data = poll_res.json()
                        if status_data["status"] == "succeeded":
                            output_url = status_data["output"][0]
                            # Download output image
                            img_data = requests.get(output_url, timeout=15).content
                            with open(output_path, "wb") as f:
                                f.write(img_data)
                            logger.info(f"FLUX Image generated successfully and saved to {output_path}")
                            return True
                        elif status_data["status"] == "failed":
                            logger.error(f"FLUX generation task failed: {status_data.get('error')}")
                            break
                    time.sleep(1.5)
        except Exception as e:
            logger.error(f"Error during FLUX generation: {str(e)}")
        return False

    def generate_image_dalle(self, prompt: str, output_path: str) -> bool:
        """Generate image using OpenAI DALL-E 3."""
        if not settings.OPENAI_API_KEY:
            return False
        
        logger.info("Generating image via OpenAI DALL-E 3...")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard"
            )
            
            img_url = response.data[0].url
            img_data = requests.get(img_url, timeout=15).content
            with open(output_path, "wb") as f:
                f.write(img_data)
            logger.info(f"DALL-E 3 Image generated successfully and saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error during DALL-E generation: {str(e)}")
        return False

    def generate_image(self, title: str, context: str, output_path: str) -> bool:
        """Main generation pipeline with fallback cascade: FLUX -> DALL-E 3 -> Local Placeholder."""
        prompt = self.generate_detailed_prompt(title, context)
        
        # 1. Try FLUX
        if self.generate_image_flux(prompt, output_path):
            return True
            
        # 2. Try DALL-E
        if self.generate_image_dalle(prompt, output_path):
            return True
            
        # 3. Local Mock Placeholder (Pillow-based design fallback)
        logger.warning("All Image Generation APIs failed. Creating local mock placeholder image.")
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (1024, 1024), color=(30, 41, 59))
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 974, 974], outline=(226, 232, 240), width=4)
            # Simple geometric elements
            draw.ellipse([300, 300, 724, 724], fill=(59, 130, 246))
            img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Could not generate placeholder image: {str(e)}")
        
        return False

    def analyze_image_with_gemini(self, image_path: str) -> str:
        """multimodal image description using Gemini 1.5 Flash."""
        if not settings.GOOGLE_API_KEY:
            return "No image understanding analysis possible. Gemini API Key missing."
            
        logger.info(f"Analyzing image {image_path} with Gemini Multimodal...")
        try:
            import google.generativeai as genai
            from PIL import Image
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            
            img = Image.open(image_path)
            prompt = (
                "Describe this news image in detail. Analyze: "
                "1. People's faces, expressions, and posture. "
                "2. Specific objects and actions happening. "
                "3. The background environment. "
                "4. Identify any irony or comedic elements. "
                "Limit the description to 3 short paragraphs."
            )
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            logger.error(f"Gemini image analysis failed: {str(e)}")
            return "Failed to analyze image content via Gemini multimodal."
