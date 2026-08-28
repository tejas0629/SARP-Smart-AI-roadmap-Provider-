# AI Learning Path Recommender

## Overview

Phase 1 is a full-stack application that turns a natural-language learning goal into a personalized AI response and structured learning roadmap. The React interface sends messages to Django; only Django calls Google Gemini.

## Tech Stack

- Frontend: React, Vite, JavaScript, CSS
- Backend: Python, Django, Django REST Framework
- AI: Google Gemini through the official `google-genai` Python SDK
- Database: MySQL through the Django ORM
- Configuration: `.env` loaded by `python-dotenv`

## Architecture

```text
React Frontend -> Django REST API -> Google Gemini
      ^                  |                |
      |                  v                v
      +----------- response JSON <--------+
                         |
                       MySQL
```

Gemini and database credentials remain server-side. The frontend receives only the assistant response and optional roadmap data.

## Project Structure

```text
backend/
  manage.py
  requirements.txt
  .venv/                 # local, ignored virtual environment
  config/                # Django project settings and URLs
  chat/                  # chat API, Gemini service, model, migration
frontend/
  package.json
  src/
    components/          # header, chat, and roadmap panels
    pages/               # dashboard page
    services/            # Django API client
.env.example             # safe configuration template
.env                     # local configuration, ignored by Git
```

## Environment Variables

Copy the template if needed:

```bash
cp .env.example .env
```

Set these values in the root `.env`:

```dotenv
GEMINI_API_KEY=
GEMINI_MODEL=
DB_NAME=ai_learning_path
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

`GEMINI_MODEL` is intentionally not given a default. Set it to a model available to your Gemini account. Also set the MySQL username and password. Django and CORS settings are included in `.env.example` for local development.

## Virtual Environment Setup

From the repository root on Linux:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

The virtual environment is ignored and must not be committed.

## MySQL Setup

Create the database before migrating:

```sql
CREATE DATABASE ai_learning_path CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Put the MySQL connection values in `.env`, then run:

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
```

## Gemini Configuration

Set both `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`. The key is read only by Django and is never sent to React. Missing values return a safe `503` response explaining what must be configured.

### Verify Gemini communication in development

With `DJANGO_DEBUG=True`, send a message through `POST /api/chat/` and watch the Django server terminal. A successful Gemini request prints:

```text
[Gemini] Calling model: <model name>
[Gemini] Response received successfully
```

If the request fails, it prints the safe message `[Gemini] API call failed: Gemini request could not be completed.`. These logs never include the API key, database credentials, authorization headers, user prompt, or full Gemini response. No Gemini request logs are emitted when `DJANGO_DEBUG=False`.

## Backend Setup

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

The API runs at `http://localhost:8000`.

## Frontend Setup

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. To use another backend URL, set `VITE_API_BASE_URL` in the frontend environment.

## API Documentation

### `POST /api/chat/`

Request:

```json
{
  "message": "I want to become a Python developer in 6 months. Give me a roadmap."
}
```

Success response:

```json
{
  "response": "...",
  "roadmap": {
    "goal": "Python Developer",
    "duration": "6 months",
    "starting_level": "Beginner",
    "steps": [],
    "projects": [],
    "milestones": [],
    "next_action": "..."
  }
}
```

The `roadmap` field is optional. Empty messages are rejected with a validation error. Gemini failures and malformed structured responses return safe error messages without secrets or stack traces.

## Phase 1 Features

- Natural-language English, Hindi, and Hinglish learning requests
- AI assistant chat with Enter-to-send, loading, error, auto-scroll, and Clear Chat states
- Dynamic structured roadmap timeline with topics, projects, and next action
- Simple `ChatMessage` persistence through Django ORM
- MySQL and Gemini configuration through environment variables

## Example Usage

```text
Mujhe 6 mahine mein Python Developer banna hai.
Mujhe roadmap de do.
```

## Current Status

The Phase 1 React UI, Django endpoint, Gemini integration, roadmap rendering, environment configuration, and setup documentation are implemented. Automated syntax/build checks are available; a live Gemini request requires valid user-provided Gemini and MySQL credentials.

## Future Roadmap

Authentication, profiles, progress tracking, course integrations, RAG, analytics, payments, notifications, and downloadable roadmaps are outside Phase 1.
