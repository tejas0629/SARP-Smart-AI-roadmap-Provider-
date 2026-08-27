import json
import re

import google.generativeai as genai
from django.conf import settings


SYSTEM_PROMPT = """
You are an AI Personalized Learning Assistant for an AI Learning Path Recommender app.
Understand the user's goal, target skill/career, timeline, current level, and daily study time when available.
Create realistic, practical learning roadmaps broken into stages, months, or weeks. Prioritize what to learn first,
suggest projects and milestones, avoid unrealistic promises, and ask one short clarification question if critical
information is missing. Respond naturally in the user's language, including English, Hindi, or Hinglish.

When the user asks for a roadmap, include a concise human-readable answer and also return a JSON object between
<ROADMAP_JSON> and </ROADMAP_JSON> with this shape:
{
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
Only put valid JSON between those tags. Do not invent secret or internal details.
""".strip()


class GeminiConfigurationError(Exception):
    pass


def _extract_roadmap(text):
    match = re.search(r'<ROADMAP_JSON>\s*(.*?)\s*</ROADMAP_JSON>', text, re.DOTALL)
    clean_text = re.sub(r'\s*<ROADMAP_JSON>.*?</ROADMAP_JSON>\s*', '\n', text, flags=re.DOTALL).strip()
    if not match:
        return clean_text, None
    try:
        return clean_text, json.loads(match.group(1))
    except json.JSONDecodeError:
        return clean_text, None


def generate_learning_response(message):
    if not settings.GEMINI_API_KEY or not settings.GEMINI_MODEL:
        raise GeminiConfigurationError('AI service is not configured. Please set Gemini environment variables.')

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
    result = model.generate_content(message)
    response_text = getattr(result, 'text', '') or 'I could not generate a response. Please try again.'
    return _extract_roadmap(response_text)
