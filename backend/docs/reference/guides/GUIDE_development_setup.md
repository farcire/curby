# Development Setup Guide

**Last Updated:** January 11, 2026  
**Purpose:** How to run Curby locally for development

---

## �� Quick Start

### Backend (Terminal 1)
```bash
cd backend
source .venv/bin/activate  # If using virtual environment
uvicorn src.api.main:app --reload --port 8000
```

### Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

---

## 📍 Access Points

- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/healthz

---

## ✅ Verify Installation

### 1. Check Backend Health
Visit http://localhost:8000/healthz - should show:
```json
{
  "status": "ok",
  "db_connection": "successful"
}
```

### 2. Test Frontend
1. Open http://localhost:5173
2. Map should load with parking data
3. Try clicking on a street segment

---

## 🔧 Troubleshooting

### Frontend Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend Issues
- Check MongoDB URI in `backend/.env`
- Verify IP whitelisted in MongoDB Atlas
- Check port 8000 available: `lsof -i :8000`

### Port Conflicts
Vite automatically uses next available port (5174, 5175, etc.)

---

## 🛑 Stopping Services

- **Backend:** `CTRL+C` in terminal running uvicorn
- **Frontend:** `CTRL+C` in terminal running npm

---

## 📝 Environment Variables

### Backend `.env`
```env
MONGODB_URI=mongodb+srv://your_user:your_password@cluster.mongodb.net/
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
SFMTA_APP_TOKEN=your_token_here
SOCRATA_APP_TOKEN=your_token_here
GEMINI_API_KEY=your_key_here
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8000
```

⚠️ **Never commit `.env` files to git!**

---

## 📚 Related Documentation

- **Backend README:** `backend/README.md`
- **Frontend README:** `frontend/README.md`
- **Project README:** Root `README.md`
- **API Documentation:** http://localhost:8000/docs (when running)

---

**Last Updated:** January 11, 2026
