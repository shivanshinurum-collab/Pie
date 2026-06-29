import os
from PIL import Image, ImageDraw, ImageFont
from src.config import settings, logger

class MemeCompositorService:
    def __init__(self):
        self.width = 1080
        self.height = 1350
        
        # Section heights
        self.header_height = 240
        self.image_height = 720
        self.footer_height = 390
        
        # Load system fonts with fallback mechanisms
        self.font_bold = self._load_font(
            ["Arial Bold.ttf", "Helvetica-Bold.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"], 52
        )
        self.font_regular = self._load_font(
            ["Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf", "LiberationSans.ttf"], 24
        )
        self.font_badge = self._load_font(
            ["Arial Bold.ttf", "Helvetica-Bold.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf"], 20
        )
        self.font_caption = self._load_font(
            ["Impact.ttf", "Arial Bold.ttf", "Helvetica-Bold.ttf", "Arial-Bold.ttf"], 52
        )

    def _load_font(self, font_names: list[str], size: int) -> ImageFont.ImageFont:
        """Find and load first available TrueType font, or fall back to default."""
        system_paths = [
            "/System/Library/Fonts/Supplemental/",  # macOS
            "/System/Library/Fonts/",              # macOS core
            "/usr/share/fonts/truetype/dejavu/",   # Linux
            "/usr/share/fonts/TTF/",               # Linux
            "C:\\Windows\\Fonts\\"                 # Windows
        ]
        
        for name in font_names:
            # Check local directory first
            if os.path.exists(name):
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    pass
            # Check system paths
            for path in system_paths:
                full_path = os.path.join(path, name)
                if os.path.exists(full_path):
                    try:
                        return ImageFont.truetype(full_path, size)
                    except Exception:
                        pass
        logger.warning(f"Could not load custom font {font_names[0]}. Falling back to Pillow default.")
        return ImageFont.load_default()

    def wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
        """Wrap text into multiple lines that fit within max_width."""
        words = text.split(" ")
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            # Render temporary line to check width
            line_str = " ".join(current_line)
            # Use getbbox for modern Pillow version compatibility (10+)
            try:
                bbox = font.getbbox(line_str)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w, _ = font.getsize(line_str)  # Fallback for old PIL versions
                
            if w > max_width:
                if len(current_line) == 1:
                    # Single word is wider than max_width, force it
                    lines.append(line_str)
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def compose_meme(
        self, 
        headline: str, 
        subheadline: str, 
        image_path: str, 
        caption: str, 
        output_path: str
    ) -> bool:
        """Compose 1080x1350 Instagram sports/news style meme canvas."""
        try:
            logger.info(f"Composing meme image canvas for: {headline[:40]}...")
            # 1. Create main canvas
            canvas = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
            draw = ImageDraw.Draw(canvas)
            
            # 2. Draw Top Section (White background - header)
            # Already white, just write text
            
            # Draw headline (Wrapped)
            headline_y = 20
            wrapped_headline = self.wrap_text(headline, self.font_bold, self.width - 80)
            
            for line in wrapped_headline[:2]:  # Limit to 2 lines for spacing safety
                draw.text((40, headline_y), line, fill=(15, 23, 42), font=self.font_bold)
                # Compute height of line
                try:
                    line_h = self.font_bold.getbbox(line)[3] - self.font_bold.getbbox(line)[1]
                except AttributeError:
                    _, line_h = self.font_bold.getsize(line)
                headline_y += line_h + 10
                
            # Draw subheadline (Gray, single line summary/subheading)
            sub_y = headline_y + 5
            wrapped_sub = self.wrap_text(subheadline, self.font_regular, self.width - 80)
            if wrapped_sub:
                draw.text((40, sub_y), wrapped_sub[0], fill=(71, 85, 105), font=self.font_regular)

            # 3. Render Center Section (News Image)
            # Image spans y-coords: [self.header_height, self.header_height + self.image_height] i.e. [330, 1050]
            if os.path.exists(image_path):
                with Image.open(image_path) as center_img:
                    # Force resize to fit center section 1080x720
                    center_img_resized = center_img.resize((self.width, self.image_height), Image.Resampling.LANCZOS)
                    canvas.paste(center_img_resized, (0, self.header_height))
            else:
                # Fill gray if missing
                draw.rectangle(
                    [0, self.header_height, self.width, self.header_height + self.image_height], 
                    fill=(203, 213, 225)
                )
                draw.text(
                    (self.width // 2 - 100, self.header_height + (self.image_height // 2)),
                    "IMAGE NOT AVAILABLE",
                    fill=(71, 85, 105),
                    font=self.font_bold
                )
                
            # 4. Draw Footer Section (Dark background - reaction caption + branding)
            footer_y = self.header_height + self.image_height  # 1050
            draw.rectangle(
                [0, footer_y, self.width, self.height], 
                fill=(15, 23, 42)  # Slate-900 base background
            )
            
            # Draw Funny Caption / Reaction
            caption_y = footer_y + 60
            # Wrap meme caption text
            wrapped_caption = self.wrap_text(caption.upper(), self.font_caption, self.width - 160)
            
            for line in wrapped_caption[:3]:  # Limit to 3 lines
                # Center-align the caption text horizontally
                try:
                    line_w = self.font_caption.getbbox(line)[2] - self.font_caption.getbbox(line)[0]
                except AttributeError:
                    line_w, _ = self.font_caption.getsize(line)
                    
                line_x = (self.width - line_w) // 2
                draw.text((line_x, caption_y), line, fill=(253, 224, 71), font=self.font_caption)  # Yellow font accent
                
                try:
                    caption_line_h = self.font_caption.getbbox(line)[3] - self.font_caption.getbbox(line)[1]
                except AttributeError:
                    _, caption_line_h = self.font_caption.getsize(line)
                caption_y += caption_line_h + 12
                
            # 5. Save the finished image
            canvas.save(output_path, "JPEG", quality=95)
            logger.info(f"Meme canvas composed successfully and saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error composing meme canvas image: {str(e)}")
            return False
