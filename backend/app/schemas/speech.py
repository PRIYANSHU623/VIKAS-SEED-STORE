from pydantic import BaseModel

class SpeechTextResponse(BaseModel):
    text: str

class TextSpeechRequest(BaseModel):
    text: str
    language: str = "en"  # "en" or "hi"
