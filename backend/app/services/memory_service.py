import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from google import genai

from app.core.config import GEMINI_API_KEY
from app.models.conversation import Conversation
from app.models.conversation_summary import ConversationSummary
from app.services.profile_service import (
    save_preference,
    update_preference,
    load_preferences,
    build_user_profile,
    build_user_profile_summary
)

logger = logging.getLogger(__name__)
def save_message(
    db: Session,
    user_id: int,
    role: str,
    message: str,
    conversation_id: str = None,
    tool_used: str = None,
    tool_output_summary: str = None,
    intent: str = None,
    topic: str = None,
):
    """
    Save a message to conversation history with metadata and compress if history gets long.
    Also extracts preferences from user messages in the background/inline.
    """
    # 1. Save to DB
    conversation = Conversation(
        user_id=user_id,
        conversation_id=conversation_id,
        role=role,
        message=message,
        tool_used=tool_used,
        tool_output_summary=tool_output_summary,
        intent=intent,
        topic=topic
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # 2. Extract preferences inline if it's a user message using rule-based (no Gemini)
    if role.lower() == "user":
        try:
            extract_and_save_preferences(db, user_id, message)
        except Exception as e:
            logger.error(f"Error extracting preferences: {e}")

    # 3. Handle automatic compression/summarization
    try:
        compress_conversation(db, user_id)
    except Exception as e:
        logger.error(f"Error compressing conversation: {e}")

    return conversation


def get_recent_messages(
    db: Session,
    user_id: int,
    limit: int = 10,
):
    """
    Return the most recent conversation messages, ordered oldest first.
    """
    messages = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )

    # Reverse so oldest appears first
    messages.reverse()

    return messages


def build_context(messages) -> str:
    """
    Convert conversation history into text for Gemini.
    """
    if not messages:
        return ""

    context = []
    for msg in messages:
        role_label = "User" if msg.role.lower() == "user" else "Assistant"
        meta = []
        if msg.intent:
            meta.append(f"Intent: {msg.intent}")
        if msg.tool_used:
            meta.append(f"Tool: {msg.tool_used}")
        
        meta_str = f" ({', '.join(meta)})" if meta else ""
        context.append(f"{role_label}{meta_str}: {msg.message}")

    return "\n".join(context)


def clear_memory(
    db: Session,
    user_id: int,
):
    """
    Delete all conversation history and summaries for a user.
    """
    db.query(Conversation).filter(Conversation.user_id == user_id).delete()
    db.query(ConversationSummary).filter(ConversationSummary.user_id == user_id).delete()
    db.commit()


def get_last_user_message(
    db: Session,
    user_id: int,
):
    """
    Return the latest user message.
    """
    return (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.role == "user",
        )
        .order_by(Conversation.created_at.desc())
        .first()
    )


def get_last_assistant_message(
    db: Session,
    user_id: int,
):
    """
    Return the latest assistant message.
    """
    return (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.role == "assistant",
        )
        .order_by(Conversation.created_at.desc())
        .first()
    )


def get_conversation_summary(db: Session, user_id: int) -> str:
    """
    Retrieve the summarized text of older conversations.
    """
    record = db.query(ConversationSummary).filter(ConversationSummary.user_id == user_id).first()
    return record.summary if record else ""


def compress_conversation(db: Session, user_id: int):
    """
    Keep the last 10 messages in the conversations table, and summarize/compress
    anything older into the ConversationSummary table.
    """
    total_count = db.query(Conversation).filter(Conversation.user_id == user_id).count()
    if total_count <= 10:
        return

    # Fetch all messages ordered oldest first
    all_msgs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.asc())
        .all()
    )

    msgs_to_compress = all_msgs[:-10]
    if not msgs_to_compress:
        return

    # Build transcript of older messages
    transcript_parts = []
    for m in msgs_to_compress:
        role_name = "Farmer" if m.role.lower() == "user" else "KrishiSathi AI"
        tool_info = f" (Tool: {m.tool_used})" if m.tool_used else ""
        transcript_parts.append(f"{role_name}{tool_info}: {m.message}")
    
    transcript = "\n".join(transcript_parts)

    # Get current summary
    summary_record = db.query(ConversationSummary).filter(ConversationSummary.user_id == user_id).first()
    old_summary = summary_record.summary if summary_record else "No previous summary."

    # Ask Gemini to merge the old summary and the new transcript
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
You are an AI system responsible for summarizing agricultural conversation history between a farmer and KrishiSathi AI.

Existing Summary of earlier conversation:
{old_summary}

New messages to incorporate:
{transcript}

Task:
Produce a concise, single-paragraph summary of the key agricultural topics discussed, crops mentioned, products recommended, and order details. Maintain important facts like specific crop names, problems diagnosed, and user preferences. Do not exceed 250 words. Do not use placeholders.
"""
    try:
        from app.services.gemini_service import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=prompt
        )
        new_summary = response.text.strip()
    except Exception as e:
        logger.error(f"Failed to generate conversation summary: {e}")
        new_summary = f"{old_summary}\n(Additional messages could not be summarized due to API error)."

    if summary_record:
        summary_record.summary = new_summary
    else:
        summary_record = ConversationSummary(user_id=user_id, summary=new_summary)
        db.add(summary_record)

    # Delete compressed messages from active table
    for m in msgs_to_compress:
        db.delete(m)

    db.commit()


def extract_and_save_preferences(db: Session, user_id: int, message: str):
    """
    Extract preference facts from user messages using local rules (no Gemini)
    and update profile.
    """
    lower_q = message.lower()
    updates = {}

    # 1. Preferred Crops
    crops = []
    for crop in ["paddy", "rice", "wheat", "maize", "cotton", "mustard"]:
        if crop in lower_q:
            crops.append("paddy" if crop == "rice" else crop)
    if crops:
        updates["preferred_crops"] = crops

    # 2. Favourite Brands
    brands = []
    for brand in ["mahadhan", "syngenta", "vikas", "bayer", "pioneer"]:
        if brand in lower_q:
            brands.append(brand.capitalize())
    if brands:
        updates["favourite_brands"] = brands

    # 3. Farm/Weather Location
    location_keywords = ["punjab", "ludhiana", "haryana", "patiala", "delhi", "amritsar", "gandhinagar", "ahmedabad"]
    found_loc = None
    for loc in location_keywords:
        if loc in lower_q:
            found_loc = loc.capitalize()
            break

    if not found_loc:
        import re
        patterns = [
            r"farm is in\s+([a-zA-Z]+)",
            r"live in\s+([a-zA-Z]+)",
            r"farm in\s+([a-zA-Z]+)",
            r"location is\s+([a-zA-Z]+)",
            r"at\s+([a-zA-Z]+)"
        ]
        for pat in patterns:
            match = re.search(pat, lower_q)
            if match:
                found_loc = match.group(1).strip().capitalize()
                break

    if found_loc:
        updates["farm_location"] = found_loc
        updates["weather_location"] = found_loc
        updates["preferred_location"] = found_loc

    # 4. Soil Type
    for soil in ["clayey", "sandy", "loam", "alluvial", "black"]:
        if soil in lower_q:
            updates["soil_type"] = soil
            break

    if updates:
        for key, val in updates.items():
            save_preference(db, user_id, key, val)