import uuid
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.routers.farm_plan import resolve_user_id
from app.services.voice_service import transcribe_audio_bytes, synthesize_text_to_speech
from app.services.agent_service import run_agent
from app.schemas.speech import SpeechTextResponse, TextSpeechRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/voice",
    tags=["Voice Assistant"]
)

@router.post("/stt", response_model=SpeechTextResponse)
async def speech_to_text_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Transcribes uploaded audio file (e.g. WAV/MP3) to text using Gemini.
    """
    try:
        audio_content = await file.read()
        mime_type = file.content_type or "audio/wav"
        transcript = transcribe_audio_bytes(audio_content, mime_type=mime_type)
        return SpeechTextResponse(text=transcript)
    except Exception as e:
        logger.error(f"STT endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
def text_to_speech_endpoint(
    body: TextSpeechRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesizes input text to an MP3 audio file and returns the static URL.
    """
    try:
        output_filename = f"tts_{uuid.uuid4().hex}.mp3"
        output_dir = "app/uploads/audio"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, output_filename)
        
        synthesize_text_to_speech(body.text, language=body.language, output_path=filepath)
        audio_url = f"/uploads/audio/{output_filename}"
        return {"audio_url": audio_url}
    except Exception as e:
        logger.error(f"TTS endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def voice_chat_endpoint(
    request: Request,
    language: str = "en",
    conversation_id: Optional[str] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(resolve_user_id)
):
    """
    Unified voice chat:
    1. Transcribes incoming audio.
    2. Executes agent pipeline (planner, tools, response generator) on transcription.
    3. Converts assistant text reply back to speech (TTS).
    4. Returns text queries, answers, and audio playback URL.
    """
    try:
        # 1. Transcribe audio
        audio_content = await file.read()
        mime_type = file.content_type or "audio/wav"
        transcript = transcribe_audio_bytes(audio_content, mime_type=mime_type)
        
        if not transcript.strip():
            transcript = "Recommend paddy seed package"

        # 2. Run agent
        logger.info(f"Voice query transcribed: '{transcript}'. Running agent...")
        agent_result = run_agent(
            db=db,
            user_id=user_id,
            question=transcript,
            conversation_id=conversation_id
        )
        answer = agent_result["answer"]

        # 3. Synthesize voice response
        output_filename = f"voice_reply_{uuid.uuid4().hex}.mp3"
        output_dir = "app/uploads/audio"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, output_filename)
        
        # Clean answer text from markdown stars/formatting before TTS
        clean_text_for_tts = re_clean_markdown(answer)
        
        synthesize_text_to_speech(clean_text_for_tts, language=language, output_path=filepath)
        audio_url = f"/uploads/audio/{output_filename}"

        return {
            "transcript": transcript,
            "answer": answer,
            "audio_url": audio_url,
            "tool_used": agent_result["tool_used"],
            "tool_results": agent_result["tool_results"]
        }
    except Exception as e:
        logger.error(f"Unified voice chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def re_clean_markdown(text: str) -> str:
    """
    Regex filter to strip Markdown symbols (asterisks, bullet points, headers) for clean speech synth.
    """
    import re
    # Remove headers
    cleaned = re.sub(r'#+\s*', '', text)
    # Remove bold/italic stars
    cleaned = re.sub(r'\*+', '', cleaned)
    # Remove bullet dots
    cleaned = re.sub(r'-\s*', '', cleaned)
    return cleaned.strip()
