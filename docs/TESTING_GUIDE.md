# 🧪 Testing Guide - Barclays Credit Intelligence Platform

**Quick Start:** Run `./run_tests.sh` for automated testing

---

## Current Status

Docker Compose is building the images. This takes 5-10 minutes on first run.

**Progress:**
- ✅ Backend dependencies installing
- ✅ Frontend dependencies installing (with --legacy-peer-deps fix)
- ⏳ Building images...
- ⏳ Starting services...

---

## Once Build Completes

### 1. Verify Services Are Running
```bash
docker-compose ps
```

**Expected Output:**
```
NAME                STATUS
barclays_backend    Up (healthy)
barclays_postgres   Up (healthy)
barclays_redis      Up (healthy)
barclays_frontend   Up
```

### 2. Run Automated Tests
```bash
./run_tests.sh
```

This script will test:
- ✅ Infrastructure (Docker, health checks)
- ✅ Backend API (registration, login, applications)
- ✅ ML Pipeline (scoring, SHAP, predictions)
- ✅ Frontend (page loads)
- ✅ Error handling

### 3. Manual Testing

#### Access Points:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

#### Test User Journey:
1. Open http://localhost:3000
2. Click "Get Started"
3. Register new user
4. Fill multi-step application form
5. View credit score result
6. Try what-if simulator
7. Chat with assistant

---

## Test Scenarios

### Scenario 1: Gig Worker (Should Approve)
```json
{
  "user_category": "gig_worker",
  "requested_amount": 50000,
  "requested_tenure_months": 12,
  "loan_purpose": "Vehicle purchase",
  "category_data": {
    "platform_name": "uber",
    "platform_tenure_months": 24,
    "avg_monthly_earnings": 35000,
    "monthly_trips": 450,
    "avg_rating": 4.7
  }
}
```

**Expected:**
- Credit Score: 680-750
- Decision: APPROVED
- Fraud Score: < 0.3

### Scenario 2: Farmer (Should Manual Review)
```json
{
  "user_category": "farmer",
  "requested_amount": 30000,
  "requested_tenure_months": 12,
  "loan_purpose": "Seeds and fertilizer",
  "category_data": {
    "land_size_acres": 5,
    "crop_type": "wheat",
    "irrigation_available": true,
    "monthly_income": 15000
  }
}
```

**Expected:**
- Credit Score: 620-680
- Decision: HOLD (manual review)
- Fraud Score: < 0.3

### Scenario 3: High Fraud Risk (Should Reject)
```json
{
  "user_category": "gig_worker",
  "requested_amount": 500000,
  "requested_tenure_months": 6,
  "loan_purpose": "Personal",
  "category_data": {
    "platform_name": "unknown",
    "platform_tenure_months": 1,
    "avg_monthly_earnings": 10000,
    "monthly_trips": 50,
    "avg_rating": 3.0
  }
}
```

**Expected:**
- Fraud Score: > 0.6
- Decision: REJECTED
- Reason: "Fraud pre-screening threshold exceeded"

---

## API Testing with cURL

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User",
    "phone_number": "+919876543210"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
```

Save the `access_token` from response!

### 3. Submit Application
```bash
export TOKEN="your-access-token-here"

curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @- <<EOF
{
  "user_category": "gig_worker",
  "requested_amount": 50000,
  "requested_tenure_months": 12,
  "loan_purpose": "Vehicle purchase",
  "category_data": {
    "platform_name": "uber",
    "platform_tenure_months": 24,
    "avg_monthly_earnings": 35000,
    "monthly_trips": 450,
    "avg_rating": 4.7,
    "vehicle_owned": true,
    "peak_hour_percentage": 65
  }
}
EOF
```

### 4. Get Credit Score
```bash
export APP_ID="application-id-from-previous-response"

curl -X GET "http://localhost:8000/api/v1/applications/$APP_ID/score" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. What-If Simulator
```bash
curl -X POST "http://localhost:8000/api/v1/applications/$APP_ID/simulate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "adjusted_income_percentage": 20,
    "adjusted_loan_amount": 60000,
    "adjusted_tenure_months": 18
  }'
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
docker-compose logs redis

# Restart all services
docker-compose restart

# Rebuild if needed
docker-compose down
docker-compose up --build
```

### Backend Errors
```bash
# Check backend logs
docker-compose logs -f backend

# Common issues:
# 1. Database not ready: Wait 30 seconds and restart
# 2. ML model not found: Check ml_pipeline/models/ directory
# 3. Import errors: Rebuild backend image
```

### Frontend Errors
```bash
# Check frontend logs
docker-compose logs -f frontend

# Common issues:
# 1. Build failed: Check TypeScript version conflict
# 2. API connection: Verify backend is running
# 3. Port conflict: Check if port 3000 is available
```

### Database Issues
```bash
# Connect to database
docker exec -it barclays_postgres psql -U admin -d barclays_credit

# Check tables
\dt

# Check users
SELECT * FROM users LIMIT 5;

# Exit
\q
```

### Redis Issues
```bash
# Connect to Redis
docker exec -it barclays_redis redis-cli

# Check connection
PING
# Should return: PONG

# Check keys
KEYS *

# Exit
exit
```

---

## Performance Testing

### Load Test with Apache Bench
```bash
# Install Apache Bench
# macOS: brew install httpd
# Ubuntu: apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test with authentication (create token first)
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/applications/
```

### Expected Performance
- Health check: < 50ms
- API endpoints: < 500ms (p95)
- ML scoring: < 2 seconds
- Frontend load: < 3 seconds

---

## Test Checklist

### Infrastructure ✓
- [ ] All 4 Docker containers running
- [ ] Health checks passing
- [ ] Database connected
- [ ] Redis connected
- [ ] Ports accessible (3000, 8000, 5432, 6379)

### Backend API ✓
- [ ] User registration works
- [ ] User login returns JWT token
- [ ] Application submission succeeds
- [ ] Credit score calculation works
- [ ] SHAP values present in response
- [ ] What-if simulator works
- [ ] Fraud detection triggers
- [ ] Policy engine validates

### Frontend ✓
- [ ] Landing page loads
- [ ] Registration form works
- [ ] Login form works
- [ ] Multi-step application form works
- [ ] All 6 user categories selectable
- [ ] Category-specific forms render
- [ ] Result page displays score
- [ ] Credit score gauge animates
- [ ] Score breakdown shows 5 pillars
- [ ] SHAP chart displays factors
- [ ] What-if simulator responds
- [ ] Chatbot opens and responds

### Admin Portal ✓
- [ ] Dashboard loads with KPIs
- [ ] Application table displays
- [ ] Filters and search work
- [ ] Application detail panel opens
- [ ] Fairness page shows DIR scores
- [ ] Audit log displays events
- [ ] Model registry shows versions
- [ ] Portfolio page shows risk metrics

### ML Pipeline ✓
- [ ] Model loads successfully
- [ ] Predictions return valid scores (300-850)
- [ ] SHAP values calculated
- [ ] Fraud scores computed
- [ ] Policy checks execute
- [ ] Auto-approve/reject works
- [ ] Manual review flagged correctly

### Integration ✓
- [ ] Complete user journey works end-to-end
- [ ] All 6 user categories work
- [ ] Fraud detection triggers appropriately
- [ ] Policy violations caught
- [ ] Audit events logged
- [ ] What-if simulator updates in real-time

---

## Success Criteria

**✅ PASS:** All tests pass, system functional  
**⚠️ PARTIAL:** Minor issues, core features work  
**❌ FAIL:** Critical failures, system not usable

---

## Next Steps After Testing

### If All Tests Pass:
1. ✅ Document any minor issues
2. ✅ Proceed with user acceptance testing
3. ✅ Configure production environment
4. ✅ Set up monitoring and alerting
5. ✅ Run security audit
6. ✅ Load test with expected traffic
7. ✅ Deploy to staging environment

### If Tests Fail:
1. ❌ Review error logs
2. ❌ Fix critical issues
3. ❌ Re-run tests
4. ❌ Document workarounds
5. ❌ Update configuration

---

## Support

- **Documentation:** See all `.md` files in project root
- **API Docs:** http://localhost:8000/docs
- **Logs:** `docker-compose logs -f`
- **Database:** `docker exec -it barclays_postgres psql -U admin -d barclays_credit`
- **Redis:** `docker exec -it barclays_redis redis-cli`

---

**🎯 Goal: Verify the entire platform works end-to-end!**

**Current Status:** Building Docker images... (5-10 minutes)

Once build completes, run: `./run_tests.sh`
