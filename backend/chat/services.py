import json
import logging

from django.conf import settings
from google import genai
from google.genai import types


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an AI Personalized Learning Assistant for an AI Learning Path Recommender app.
Understand the user's goal, target skill or career, timeline, current level, and daily study time when available.
Create realistic, practical learning roadmaps broken into logical stages. Prioritize what to learn first, suggest
topics, practical projects, milestones, and the next action. Avoid unrealistic promises and ask one short
clarification question only when critical information is genuinely missing. Respond naturally in English, Hindi,
or Hinglish, matching the user's language. Keep the response concise and useful.

Return only valid JSON in this shape:
{
  "response": "concise natural-language answer",
  "roadmap": {
    "goal": "string",
    "duration": "string",
    "starting_level": "string",
    "steps": [
      {"title": "string", "duration": "string", "description": "string", "topics": ["string"]}
    ],
    "projects": ["string"],
    "milestones": ["string"],
    "next_action": "string"
  }
}
Use null for roadmap when the user has not asked for a learning path or important details are missing.
""".strip()


class GeminiConfigurationError(Exception):
    pass


class GeminiResponseError(Exception):
    pass


def generate_learning_response(message):
    if not settings.GEMINI_API_KEY:
        raise GeminiConfigurationError('Gemini API key is not configured. Set GEMINI_API_KEY in .env.')
    if not settings.GEMINI_MODEL:
        raise GeminiConfigurationError('Gemini model is not configured. Set GEMINI_MODEL in .env.')

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        if settings.DEBUG:
            logger.info('[Gemini] Calling model: %s', settings.GEMINI_MODEL)
        result = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type='application/json',
            ),
        )
        if settings.DEBUG:
            logger.info('[Gemini] Response received successfully')
    except Exception:
        if settings.DEBUG:
            logger.error('[Gemini] API call failed: Gemini request could not be completed.')
        raise
    response_text = (getattr(result, 'text', '') or '').strip()
    if not response_text:
        raise GeminiResponseError('Gemini returned an empty response.')

    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise GeminiResponseError('Gemini returned an invalid structured response.') from exc

    if not isinstance(payload, dict) or not isinstance(payload.get('response'), str):
        raise GeminiResponseError('Gemini returned an incomplete structured response.')

    roadmap = payload.get('roadmap')
    if roadmap is not None and not isinstance(roadmap, dict):
        raise GeminiResponseError('Gemini returned an invalid roadmap.')
    return payload['response'].strip(), roadmap
