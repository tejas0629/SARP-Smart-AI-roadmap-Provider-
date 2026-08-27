# AI Learning Path Recommender

Phase 1 full-stack app for generating personalized learning roadmaps through a React chat UI, Django REST API, and Google Gemini.

## Architecture

React frontend → Django REST API → Google Gemini API. Gemini credentials and MySQL credentials stay server-side in `.env`.

## Setup

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Fill in Gemini and MySQL values in `.env`.

3. Install backend dependencies and run migrations:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

4. Install frontend dependencies and start Vite:

```bash
cd frontend
npm install
npm run dev
```

5. Open `http://localhost:5173` and ask for a roadmap, for example: `I want to become a Python Developer in 6 months. Give me a roadmap.`

## API

`POST /api/chat/`

```json
{
  "message": "I want to become a Python developer in 6 months. Give me a roadmap."
}
```

Returns an AI response and, when Gemini provides it, structured roadmap data for the learning path panel.
