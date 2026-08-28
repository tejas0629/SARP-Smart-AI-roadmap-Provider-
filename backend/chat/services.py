import json
import logging
import socket

from django.conf import settings
from google import genai
from google.genai import types
from groq import Groq


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


class GroqConfigurationError(Exception):
    pass


class GroqResponseError(Exception):
    pass


def _parse_provider_response(response_text, provider):
    response_text = (response_text or '').strip()
    if not response_text:
        raise GeminiResponseError(f'{provider} returned an empty response.')

    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise GeminiResponseError(f'{provider} returned an invalid structured response.') from exc

    if not isinstance(payload, dict) or not isinstance(payload.get('response'), str):
        raise GeminiResponseError(f'{provider} returned an incomplete structured response.')

    roadmap = payload.get('roadmap')
    if roadmap is not None and not isinstance(roadmap, dict):
        raise GeminiResponseError(f'{provider} returned an invalid roadmap.')
    return payload['response'].strip(), roadmap


def _is_temporary_gemini_error(exc):
    status_code = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
    if hasattr(status_code, 'value'):
        status_code = status_code.value
    if isinstance(status_code, int) and (status_code == 429 or 500 <= status_code <= 599):
        return True

    error_name = type(exc).__name__.lower()
    temporary_names = (
        'ratelimit',
        'resourceexhausted',
        'toomanyrequests',
        'serviceunavailable',
        'internalserver',
        'deadlineexceeded',
        'timeout',
        'connection',
    )
    return isinstance(exc, (ConnectionError, TimeoutError, socket.timeout)) or any(
        name in error_name for name in temporary_names
    )


def _generate_groq_response(message):
    if not settings.GROQ_API_KEY:
        raise GroqConfigurationError('Groq API key is not configured. Set GROQ_API_KEY in .env.')
    if not settings.GROQ_MODEL:
        raise GroqConfigurationError('Groq model is not configured. Set GROQ_MODEL in .env.')

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        result = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': message},
            ],
            response_format={'type': 'json_object'},
        )
    except Exception as exc:
        logger.error('[Groq] Fallback provider failed.')
        raise GroqResponseError('The fallback AI service is temporarily unavailable.') from exc

    try:
        response_text = result.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise GroqResponseError('Groq returned an incomplete structured response.') from exc

    try:
        return _parse_provider_response(response_text, 'Groq')
    except GeminiResponseError as exc:
        raise GroqResponseError(str(exc)) from exc


def generate_learning_response(message):
    if not settings.GEMINI_API_KEY:
        raise GeminiConfigurationError('Gemini API key is not configured. Set GEMINI_API_KEY in .env.')
    if not settings.GEMINI_MODEL:
        raise GeminiConfigurationError('Gemini model is not configured. Set GEMINI_MODEL in .env.')

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
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
    except Exception as exc:
        if settings.DEBUG:
            logger.error('[Gemini] API call failed: Gemini request could not be completed.')
        if _is_temporary_gemini_error(exc):
            logger.warning('[Gemini] Primary provider unavailable. Switching to Groq fallback.')
            return _generate_groq_response(message)
        raise

    return _parse_provider_response(getattr(result, 'text', ''), 'Gemini')
