# Deployment Quick Reference

**Last Updated:** January 11, 2026  
**Status:** Currently deployed to Render.com

---

## 🌐 Current Production Setup

**Backend API:** Deployed on Render.com  
**Database:** MongoDB Atlas  
**Frontend:** [To be documented]

---

## 🚀 Backend Deployment (Render.com)

### Current Deployment
- **Service:** Render.com Web Service
- **Repository:** GitHub (elegant-lynx-play)
- **Branch:** `main`
- **Auto-deploy:** Enabled on push to main

### Build Configuration
```
Build Command: pip install -r requirements.txt
Start Command: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
Root Directory: backend/
```

### Environment Variables (Set in Render Dashboard)
```
MONGODB_URI=<from MongoDB Atlas>
CORS_ORIGINS=<frontend URL>
SFMTA_APP_TOKEN=<from SFMTA>
SOCRATA_APP_TOKEN=<from SFMTA>
```

### Health Check
- **Endpoint:** `/healthz`
- **Expected Response:** `{"status": "ok", "db_connection": "successful"}`

---

## 🗄️ MongoDB Atlas

### Current Setup
- **Cluster:** [Cluster name/details]
- **Database:** `parking_db`
- **Collections:** `street_segments`, `parking_regulations`, `error_reports`

### Network Access
- Render.com IPs whitelisted
- Or: 0.0.0.0/0 (allow all - not recommended for production)

### Initial Data Load
```bash
# One-time setup after database creation
python scripts/ingestion/ingest_data_cnn_segments_v2.py
```

**Duration:** ~30-45 minutes  
**Result:** 34,324 street segments with parking data

---

## 🔄 Deployment Process

### Deploy New Version
1. Push code to `main` branch
2. Render automatically detects and deploys
3. Monitor build logs in Render dashboard
4. Verify health endpoint after deployment

### Rollback
1. Go to Render dashboard → Deployments
2. Select previous successful deployment
3. Click "Redeploy"

---

## 📊 Monitoring

**API Documentation:** `<backend-url>/docs`  
**Health Check:** `<backend-url>/healthz`  
**Render Logs:** Available in dashboard

---

## ⚠️ Common Issues

### Issue: Database Connection Failed
**Solution:** Check MongoDB Atlas network access whitelist

### Issue: SFMTA API Rate Limit
**Solution:** Reduce ingestion frequency, add delays in script

### Issue: Build Failed
**Solution:** Check requirements.txt for conflicts, review build logs

---

## 📝 TODO: Complete Documentation Needed

This is a quick reference. Full deployment guide should include:
- [ ] Exact Render.com configuration steps
- [ ] MongoDB Atlas setup from scratch
- [ ] Environment variable complete list with examples
- [ ] Frontend deployment process
- [ ] DNS/domain configuration
- [ ] SSL certificate setup
- [ ] Monitoring and alerting setup
- [ ] Backup and disaster recovery procedures

---

**For detailed setup:** See `GUIDE_development_setup.md` for local development
**For operations:** See operational scripts in `backend/` (run.sh, backup_database.sh, etc.)
