# Teammate Setup — MedBridge Backend

## 1. Create virtual environment

python -m venv .venv
.\.venv\Scripts\Activate.ps1

## 2. Install dependencies

pip install -r requirements.txt

## 3. Create environment file

copy .env.example .env

Fill in the credentials provided privately.

Required variables:

- SUPABASE_URL
- SUPABASE_ANON_KEY
- DATABASE_URL
- GROQ_API_KEY

## 4. Start the FastAPI server

uvicorn app.main:app --reload

Then open:

http://127.0.0.1:8000/docs

## 5. Run integration tests

pytest tests/integration/ -v --timeout=60

If anything fails, copy the full error output.
