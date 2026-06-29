import os
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip
import moviepy.video.fx as vfx
from src.config import settings, logger

class VideoGeneratorService:
    def __init__(self):
        pass

    def generate_voiceover_audio(self, text: str, output_path: str) -> bool:
        """Convert voiceover script text to speech MP3 file using gTTS."""
        logger.info("Generating voiceover text-to-speech audio...")
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(output_path)
            logger.info(f"Voiceover audio saved successfully to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate TTS audio: {str(e)}")
            return False

    def build_zoom_effect(self, clip, duration, zoom_ratio=0.08):
        """Apply a slow, smooth zoom-in Ken Burns effect over time."""
        # Use MoviePy v2.x with_effects for resizing over time
        return clip.with_effects([vfx.Resize(lambda t: 1.0 + zoom_ratio * (t / duration))])

    def create_reel(
        self, 
        image_path: str, 
        voiceover_text: str, 
        duration: int, 
        output_path: str
    ) -> bool:
        """Compile a dynamic Instagram Reel video (MP4) from a static meme image."""
        audio_path = output_path.replace(".mp4", ".mp3")
        audio_clip = None
        video_clip = None
        
        try:
            logger.info(f"Creating {duration}s Instagram Reel for meme image: {image_path}...")
            
            # 1. Try to generate voiceover audio
            has_audio = False
            if voiceover_text:
                has_audio = self.generate_voiceover_audio(voiceover_text, audio_path)
            
            # 2. Create static image clip
            if not os.path.exists(image_path):
                logger.error(f"Base meme image does not exist: {image_path}")
                return False
                
            img_clip = ImageClip(image_path)
            img_clip = img_clip.with_duration(duration)
            
            # 3. Apply motion graphics zoom effect
            # Note: We need to enable scaling/resizing which requires PIL or NumPy backend
            img_clip = self.build_zoom_effect(img_clip, duration)
            
            # 4. Attach audio track if available
            if has_audio and os.path.exists(audio_path):
                try:
                    audio_clip = AudioFileClip(audio_path)
                    # If audio is longer than requested duration, truncate audio. 
                    # If shorter, keep clip length.
                    audio_duration = audio_clip.duration
                    if audio_duration > duration:
                        audio_clip = audio_clip.subclipped(0, duration)
                    else:
                        # Extend image clip duration to match the audio
                        img_clip = img_clip.with_duration(audio_duration)
                    
                    video_clip = img_clip.with_audio(audio_clip)
                    logger.info("Attached synthesized voiceover audio to the Reel.")
                except Exception as audio_err:
                    logger.error(f"Error attaching audio track: {str(audio_err)}")
                    video_clip = img_clip
            else:
                video_clip = img_clip
            
            # 5. Write final video file
            # Use libx264 for high compatibility, set FPS=24 for smooth scaling animation
            logger.info("Writing video file with moviepy...")
            video_clip.write_videofile(
                output_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac" if has_audio else None,
                logger=None  # Suppress moviepy progress bar logs
            )
            
            # Clean up temporary audio file if created
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
                    
            logger.info(f"Successfully generated Instagram Reel video: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate video reel: {str(e)}")
            # Cleanup on failure
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
            return False
        finally:
            # Ensure clip resources are closed
            if audio_clip:
                audio_clip.close()
            if video_clip:
                video_clip.close()

    def get_music_suggestions(self, sentiment: str) -> dict:
        """Provide trending background music tags based on post sentiment."""
        suggestions = {
            "Positive": {
                "genre": "Upbeat / Funk / Pop",
                "tracks": ["Future - Life is Good (Instrumental)", "Pharrell Williams - Happy (Chill Mix)"],
                "vibe": "Energetic, feel-good, motivational"
            },
            "Negative": {
                "genre": "Dark Synth / Cinematic Drone",
                "tracks": ["Hans Zimmer - Time (Remix)", "Aloboi - A Pleasing Smile"],
                "vibe": "Dramatic, tense, serious"
            },
            "Chaos": {
                "genre": "Phonk / Hard Bass",
                "tracks": ["Kordhell - Murder In My Mind", "DVRST - Close Eyes"],
                "vibe": "Savage, fast-paced, high energy"
            },
            "Neutral": {
                "genre": "Lo-Fi / Chillhop / Jazz",
                "tracks": ["Lofi Girl - Standard Study Beat", "Nujabes - Feather (Instrumental)"],
                "vibe": "Relaxed, informational, casual"
            }
        }
        return suggestions.get(sentiment, suggestions["Neutral"])
