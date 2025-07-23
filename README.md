# News Summarizer & Fake News Detector — Backend

This is the **Django REST API backend** for the News Summarizer & Fake News Detector platform.

---

## 🧠 What It Does

- Parses & summarizes news articles (HuggingFace)
- Detects likely fake news (zero-shot classification)
- Logs all queries and user feedback
- Powers secure admin dashboard & analytics

---

## ⚙️ Tech Stack

- Python 3, Django, Django REST Framework
- HuggingFace Inference API (BART, MNLI)
- Token authentication for admin access
- SQLite/Postgres (auto-switching)
- CORS for frontend integration

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Griffins2005/News-Summarizer-Backend.git
cd News-Summarizer-Backend
2. Install Dependencies
bash
Copy
Edit
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. Environment Variables
HF_API_KEY (required) — HuggingFace API key for summaries & fake news detection

DJANGO_SECRET_KEY (recommended)

DATABASE_URL (optional, for production/Postgres)

Example: see .env.example

4. Migrate & Create Superuser
bash
Copy
Edit
python manage.py migrate
python manage.py createsuperuser
5. Run the Server
bash
Copy
Edit
python manage.py runserver
Visit: http://localhost:8000/api/

🔑 API Endpoints
POST /api/analyze/ — Summarize/check news (URL/text)

POST /api/feedback/ — Submit user feedback

POST /api/admin-token/ — Obtain token (admin login)

POST /api/admin-check/ — Verify admin privileges

GET /api/all-history/ — Query history (admin)

GET /api/all-feedback/ — User feedback (admin)

Admin endpoints require token authentication.

🛠️ Deployment
Deployable to Render, Heroku, Fly, etc.

Set ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS for your frontend

Use Gunicorn/Whitenoise for static serving (see settings.py)

🌐 Frontend
For UI and usage instructions, see:
https://github.com/Griffins2005/News-Summarizer

📝 License
MIT

Built by Griffins Kiptanui Lelgut
