# PrepPilot

AI-powered interview coaching platform that helps users practice realistic mock interviews and improve through structured feedback.

## 🚀 Features (MVP)

- 🔐 User authentication (JWT) + guest access
- 🎯 Interview type selection (DSA, HR, ML, Backend, Frontend)
- 💬 Structured interview session with timed Q&A
- 🤖 AI-powered question generation (Google Gemini)
- 📊 End-of-interview feedback report
- 📈 Dashboard with performance tracking
- 📄 Resume upload & personalized questions

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14/15 (App Router, TypeScript) + Tailwind CSS + Framer Motion + shadcn/ui |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy |
| AI | Google Gemini API |
| Deployment | Docker + Railway/Render |
| Auth | JWT (python-jose + bcrypt) |

## 📁 Project Structure

```
PrepPilot/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── docker-compose.yml
└── README.md
```

## 🐳 Quick Start (Docker)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🛠️ Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
Using Docker (Recommended):
```bash
docker-compose up frontend --build
```
Or locally (requires Node.js):
```bash
cd frontend
npm install
npm run dev
```

## 📄 License

MIT
