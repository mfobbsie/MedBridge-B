# MedBridge — Backend

AI-Powered Patient Health Companion — Backend API

## Project Information

**Project Name:** MedBridge  
**Team Name:** Team 2 (Disco)  
**Cohort / Sprint:** Tech Residency 43 / Sprint 1–2  
**Team Members:** Kathy Matos Linares, Kyle Babington, James Hightower, Mary Fobbs-Guillory, Melodie Fan, Riman Bastola  
**Tech Stack:** Python 3.11+, FastAPI, Supabase (PostgreSQL), Groq API (Llama 3.3 70B), SMART on FHIR / Epic sandbox, Render

## Project Overview

MedBridge helps patients understand their health records through AI-powered summaries, chat, and care coordination tools.

- **Problem:** Medical documents are dense and hard for patients to interpret on their own.
- **Target user:** Patients managing chronic conditions who need plain-language explanations of labs, medications, and visit notes.
- **Core features completed:** Document upload (PDF/OCR), AI summaries, document chat, reminders, care team contacts, follow-ups, provider resources, user settings, analytics/KPI dashboards, and Row Level Security across all tables.

## Setup & Documentation

- **Clone:** `git clone https://github.com/Coding-Temple-Tech-Residency/MedBridge-B.git`
- **Setup guide:** See [TEAMMATE_SETUP.md](TEAMMATE_SETUP.md)
- **Environment variables:** Copy `.env.example` to `.env` and fill in Supabase + Groq credentials (never commit `.env`)
- **API documentation:** Run `uvicorn app.main:app --reload` and open `http://localhost:8000/docs`, or see [FRONTEND_API.md](FRONTEND_API.md)
- **Postman:** Import `postman/MedBridge-API.postman_collection.json` and `postman/MedBridge-Local.postman_environment.json`
- **Migrations:** Run SQL files in `migrations/` in order (001 through 006) in the Supabase SQL Editor
- **Deployment:** Render (free tier) — link TBD

## Project Structure

    MedBridge-B/
      migrations/           SQL schema migrations (run in order)
      seed/                 Synthea synthetic data loader
      data/                 FHIR mapper, data inspector, verifier
      fhir_oauth_spike/     SMART on FHIR OAuth proof of concept
      app/                  FastAPI application
      postman/              API collection for local testing
      tests/                Unit, integration, and security tests

## Team

| Name                | Role                     |
| ------------------- | ------------------------ |
| Kathy Matos Linares | Backend + Data Analytics |
| Kyle Babington      | Backend                  |
| James Hightower     | Frontend                 |
| Mary Fobbs-Guillory | Frontend                 |
| Melodie Fan         | Frontend                 |
| Riman Bastola       | Cybersecurity            |

## Notes

- Synthea synthetic data and Epic FHIR sandbox connection are in progress.
- `sample_responses/api_responses.json` contains placeholder shapes; real data loading may adjust response fields slightly.
- Two migration files share the `006` prefix: run `006_user_settings.sql` and `006_app_events.sql` after 005.
- Backend server-side operations require `SUPABASE_SERVICE_ROLE_KEY` in `.env` (server only — never expose to frontend).

## Development Standards Reminder

All submissions should reflect professional engineering standards:

- Write clean, readable, and modular code
- Use clear naming conventions
- Remove unused files, variables, and console logs
- Follow consistent formatting and linting practices
- Write meaningful commit messages
- Keep branches organized and avoid pushing broken code to main
- Review teammate pull requests respectfully and constructively

Your repository should be organized, understandable, and demo-ready.

## Intellectual Property Notice

This project was created as part of a Coding Temple Tech Residency. All work produced during the residency is considered the intellectual property of Coding Temple or the sponsoring employer, unless otherwise stated in a signed agreement. By contributing to this project, you acknowledge and agree to these terms.

Tech Residency 43 — Coding Temple — June–July 2026
