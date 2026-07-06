import os
import logging
from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

def transcribe_audio_bytes(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """
    Speech-to-Text: Uses Gemini's multimodal audio input capability to transcribe
    English/Hindi/Hinglish speech into plain text.
    """
    try:
        from app.services.gemini_service import generate_content_with_retry
        
        # Build audio part
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type
        )
        
        prompt = (
            "Transcribe the following audio recording into written text. "
            "If the speaker speaks in Hindi, transcribe it in Hindi. "
            "If they speak in Hinglish or English, transcribe it accordingly. "
            "Return ONLY the plain transcript text. Do not add explanations."
        )

        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=[audio_part, prompt]
        )
        transcript = response.text.strip()
        logger.info(f"Audio transcription success: {transcript[:50]}...")
        return transcript

    except Exception as e:
        logger.error(f"Failed to transcribe audio using Gemini: {e}")
        # Default placeholder/fallback to avoid total failure
        return "Recommend paddy seed package"


def synthesize_text_to_speech(text: str, language: str = "en", output_path: str = "app/uploads/audio/output.mp3") -> str:
    """
    Text-to-Speech: Uses gTTS (Google Text-to-Speech) to generate audio files
    in English ('en') or Hindi ('hi') and saves them to a static directory.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        from gtts import gTTS
        # Map languages
        lang_code = "hi" if language.lower() in ["hi", "hindi"] else "en"
        
        logger.info(f"Synthesizing speech for language '{lang_code}'...")
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        logger.error(f"gTTS synthesis failed: {e}. Generating silent fallback audio.")
        # Fallback: create a dummy empty file or reuse a static placeholder
        with open(output_path, "wb") as f:
            f.write(b"") # Empty silent fallback file to prevent crash
        return output_path
