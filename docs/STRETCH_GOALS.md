# MedBridge Stretch Goals

Everything listed here is out of scope for the Demo Day MVP.
The schema, architecture, and code are designed so these can be added
without structural rework.

---

## Priority 1 — High Impact, Moderate Effort

### Reminder Service

**What:** Detect dates/appointments in uploaded documents, create reminders,
send email notifications.

**Schema:** Already exists (`reminders`, `follow_ups`, `notifications` tables).

**Implementation path:**
1. Add date extraction to extraction_service.py using regex or Groq
2. Build `reminder_service.py`
3. Add `POST/GET/PATCH /reminders` routes (stubs ready in router)
4. Email: Supabase Edge Functions or Resend API

**Effort:** 2–3 days

---

### Caregiver Sharing

**What:** Allow a patient to share document summaries with a family member
or caregiver (view-only access).

**Schema:** `trusted_contacts` table already exists.

**Implementation path:**
1. Add `POST /contacts` to create a trusted contact
2. Generate a share token with expiry
3. `GET /shared/{token}` returns the summary without auth (or with a guest token)
4. Add sharing_enabled flag to summaries table

**Effort:** 2–3 days

---

### Feedback Rating Analytics

**What:** Surface the `feedback_rating` data we're already collecting.

**schema:** `kpi_chatbot_usage` view already built.

**Implementation path:**
1. Add `GET /admin/kpis` endpoint (service-role only)
2. Return kpi_chatbot_usage, kpi_upload_outcomes, kpi_summary_engagement
3. Frontend dashboard panel for team to monitor quality

**Effort:** 1 day

---

## Priority 2 — High Impact, Higher Effort

### Semantic Chunk Retrieval (pgvector)

**What:** Replace keyword-based chunk retrieval with embedding similarity.
Dramatically improves Q&A accuracy on long or complex documents.

**Current state:** `simple_keyword_retrieval` in chunking_service.py is the
placeholder. The `document_chunks` table is already built.

**Implementation path:**
1. Enable pgvector extension in Supabase: `CREATE EXTENSION vector`
2. Add `embedding vector(1536)` column to `document_chunks`
3. On chunk creation, call Groq or OpenAI embeddings API to generate vectors
4. On Q&A, embed the question and do cosine similarity search:
   ```sql
   SELECT chunk_text FROM document_chunks
   WHERE document_id = $1
   ORDER BY embedding <=> $2  -- pgvector cosine operator
   LIMIT 5;
   ```
5. Replace `simple_keyword_retrieval` call in chat_service.py

**Effort:** 2–3 days

---

### Multi-Language Summaries

**What:** Generate summaries in the user's preferred language.

**Current state:** `preferred_language` column already in `user_profiles`.

**Implementation path:**
1. Read `preferred_language` from user_profiles at summary generation time
2. Add language instruction to the summary system prompt:
   `"Respond in {language}. If the document is in a different language, translate to {language}."`
3. Test with Spanish (highest priority for US patient population)

**Effort:** 1–2 days (if Groq handles the target language well)

---

### Background Processing Queue

**What:** Move document processing off the request thread.
Required for production — currently runs synchronously.

**Current state:** `_process_document()` in document_service.py is called
inline. FastAPI `BackgroundTasks` is the simplest upgrade.

**Implementation path (FastAPI BackgroundTasks — minimal change):**
```python
# In the upload route:
background_tasks.add_task(_process_document, document_id, user_id, file_bytes, mime_type)
```

**Implementation path (production — Supabase Edge Functions or Redis Queue):**
1. Upload stores file and record, returns immediately
2. Supabase Database Webhook fires on INSERT to health_records
3. Triggers an Edge Function that calls the extraction/summary services
4. Frontend polls as today

**Effort:** BackgroundTasks = 1 hour. Full queue = 2–3 days.

---

## Priority 3 — Future Roadmap

### SMART on FHIR Integration

**What:** Pull records directly from patient portals (MyChart, Epic, etc.)

**Current state:** `fhir_oauth_spike/main.py` exists in the repo.

**Implementation path:**
1. Complete the OAuth 2.0 PKCE flow in the spike
2. Map FHIR R4 resources (Observation, DiagnosticReport, DocumentReference)
   to health_records rows
3. Treat FHIR-sourced records identically to uploaded documents from
   extraction onward

**Effort:** 3–5 days + institutional partnership for live FHIR endpoints

---

### Appointment Preparation

**What:** Generate "questions to ask your doctor" based on the uploaded
document — directly addressing the stakeholder's communication gap insight.

**Implementation path:**
1. New endpoint: `POST /documents/{id}/prep`
2. New prompt in summary_service.py:
   ```
   Based on this document, suggest 3-5 plain-language questions
   the patient could ask their healthcare provider at their next visit.
   Focus on things that are unclear, concerning, or require follow-up.
   Do NOT suggest diagnoses or treatments.
   ```
3. Store in a new `appointment_prep` table
4. Return alongside the summary

**Effort:** 1–2 days (the prompt work is straightforward)

---

### Wearable Integration

**What:** Accept data from Apple Health, Fitbit, Google Fit.

**Schema:** `trusted_contacts`, `encounters` can accommodate this.

**Effort:** 3–5 days per platform. Lower priority than FHIR.

---

## What Never Gets Built

Per the explicit out-of-scope list in the Backend MVP Build Plan:

- Diagnostic recommendations
- Treatment suggestions
- Medication adjustment guidance
- Clinical decision support
- Real-time provider network
- Health scoring or predictive analytics
