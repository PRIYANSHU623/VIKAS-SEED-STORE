import os
import time
import random
import re
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError, ClientError

logger = logging.getLogger(__name__)

# Global client reference
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client

def generate_content_with_retry(client, model, contents, config=None, max_retries=3, initial_delay=2.0):
    """
    Calls client.models.generate_content with exponential backoff and random jitter.
    Retries on 429 (Rate Limit), 503 (Service Unavailable), and timeouts.
    Respects Retry-After header or retry delay from the error message.
    """
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Gemini API request (attempt {attempt + 1}/{max_retries + 1})...")
            # Generate request
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response
        except Exception as e:
            last_error = e
            err_str = str(e)
            is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
            is_503 = "503" in err_str or "unavailable" in err_str.lower() or "overloaded" in err_str.lower()
            is_timeout = isinstance(e, TimeoutError) or "timeout" in err_str.lower() or "deadline" in err_str.lower()
            
            if (is_429 or is_503 or is_timeout) and attempt < max_retries:
                # 1. Respect Retry-After / retry delay from error message if possible
                retry_seconds = None
                
                # Check for "Please retry in X.Y s" or similar in error string
                match = re.search(r"retry in ([0-9.]+)s", err_str, re.IGNORECASE)
                if match:
                    retry_seconds = float(match.group(1))
                else:
                    # Check for Retry-After header format
                    match_header = re.search(r"retry-after:?\s*([0-9.]+)", err_str, re.IGNORECASE)
                    if match_header:
                        retry_seconds = float(match_header.group(1))
                
                # 2. Determine sleep duration
                if retry_seconds is not None:
                    sleep_time = retry_seconds + random.uniform(0.1, 1.0)
                    logger.warning(f"Rate limit hit. Extracted retry wait from error: {retry_seconds}s. Waiting {sleep_time:.2f}s before retry...")
                else:
                    # Exponential backoff with jitter
                    sleep_time = (delay * (2 ** attempt)) + random.uniform(0.1, 1.0)
                    logger.warning(f"Error hit (429/503/timeout). Waiting {sleep_time:.2f}s before retry...")
                
                logger.info(f"Gemini retry trigger. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Gemini API call failed permanently after {attempt + 1} attempts. Error: {e}")
                raise e

    if last_error:
        raise last_error

SYSTEM_PROMPT = """
You are KrishiSathi AI, a helpful agricultural assistant.
You help farmers with:
- Seeds selection and management
- Fertilizers usage and layout metrics
- Herbicides and Pesticides application guidelines
- Crop diseases identification and treatment
- Agriculture best practices

Always answer clearly and practically. If unsure, say so.
"""

def ask_gemini(message: str) -> str:
    try:
        client = get_client()
        
        # Use native configuration objects to pass system instructions cleanly
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
        )
        
        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=message,
            config=config
        )
        
        return response.text

    except ValueError as e:
        print(f"Configuration Error: {e}")
        return "KrishiSathi AI is not configured. Please set the GEMINI_API_KEY in the backend .env file."

    except (ServerError, APIError) as e:
        print(f"Gemini API Exception Caught: {e}")
        return "KrishiSathi AI is currently experiencing heavy server traffic. Please try submitting your agricultural query again in a moment."
        
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return "An unexpected error occurred while processing your message. Please check back shortly."