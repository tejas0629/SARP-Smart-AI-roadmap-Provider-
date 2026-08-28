import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

query = 'best beginner Java syntax tutorial'
model = os.environ['GEMINI_MODEL']
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

try:
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
except Exception as exc:
    detail = str(exc).replace(os.environ['GEMINI_API_KEY'], '[REDACTED]')
    print(f'ERROR {type(exc).__name__}: {detail}')
    raise

print(response.text or '')
metadata = response.candidates[0].grounding_metadata if response.candidates else None
for chunk in metadata.grounding_chunks if metadata else []:
    web = getattr(chunk, 'web', None)
    if web and getattr(web, 'uri', None):
        print(f'URL {web.uri}')
