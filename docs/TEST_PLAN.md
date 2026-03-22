# 🧪 Complete End-to-End Test Plan

This document guides you through testing the entire Barclays Credit Intelligence Platform.

---

## Pre-Test Checklist

- [ ] Docker and Docker Compose installed
- [ ] .env file configured
- [ ] Ports 3000, 8000, 5432, 6379 available
- [ ] 8GB RAM available
- [ ] 10GB disk space available

---

## Phase 1: Infrastructure Test (5 minutes)

### Step 1: Start All Services
```bash
cd barclays-credit-platform
./start.sh
```

**Expected Output:**
```
✓ Starting PostgreSQL...
✓ Starting Redis...
✓ Starting Backend...
✓ Starting Frontend...
All services are running!
```

### Step 2: Verify Services
```bash
# Check running containers
docker-compose ps

# Should show 4 services: db, redis, backend, frontend
```

### Step 3: Health Checks
```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Database health
curl http://localhost:8000/health/db
# Expected: {"status":"healthy","database":"connected"}

# Redis health
curl http://localhost:8000/health/redis
# Expected: {"status":"healthy","redis":"connected"}
```

**✅ Pass Criteria:** All 4 services running, all health checks return "healthy"

---

## Phase 2: Backend API Test (10 minutes)

### Test 1: User Registration
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

**Expected Response:**
```json
{
  "user_id": "uuid-here",
  "email": "test@example.com",
  "full_name": "Test User",
  "message": "User registered successfully"
}
```

### Test 2: User Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Save the access_token for next tests!**

### Test 3: Submit Loan Application (Gig Worker)
```bash
export TOKEN="your-access-token-here"

curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
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
  }'
```

**Expected Response:**
```json
{
  "application_id": "uuid-here",
  "application_number": "APP-202603-XXXXXX",
  "status": "ml_scored",
  "fraud_check_passed": true,
  "fraud_score": 0.15,
  "next_step": "disbursal preparation"
}
```

**Save the application_id!**

### Test 4: Get Credit Score
```bash
export APP_ID="your-application-id-here"

curl -X GET "http://localhost:8000/api/v1/applications/$APP_ID/score" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "credit_score": 720,
  "score_band": "medium",
  "probability_of_default": 0.18,
  "risk_tier": "medium",
  "eligibility": "APPROVED",
  "suggested_amount": 50000,
  "suggested_tenure_months": 12,
  "interest_rate_min": 12.5,
  "interest_rate_max": 15.0,
  "estimated_emi_min": 4450,
  "estimated_emi_max": 4550,
  "income_stability_score": 18,
  "repayment_capacity_score": 22,
  "spending_data_score": 12,
  "profile_completeness_score": 8,
  "alternative_data_score": 15,
  "top_positive_factors": ["income_stability", "platform_tenure"],
  "top_negative_factors": ["no_credit_history"],
  "shap_summary": "Decision: auto_approve_low_risk | Confidence: high"
}
```

### Test 5: What-If Simulator
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

**Expected Response:**
```json
{
  "adjusted_credit_score": 735,
  "adjusted_probability_of_default": 0.16,
  "adjusted_eligibility": "APPROVED",
  "adjusted_approved_amount": 60000,
  "adjusted_interest_rate_min": 12.0,
  "adjusted_interest_rate_max": 14.5,
  "adjusted_emi": 3800,
  "score_change": 15,
  "pd_change": -0.02
}
```

**✅ Pass Criteria:** All API calls return 200 status, credit score between 300-850, SHAP values present

---

## Phase 3: Frontend Test (15 minutes)

### Test 1: Access Frontend
1. Open browser: http://localhost:3000
2. **Expected:** Landing page with hero section and features

### Test 2: User Registration
1. Click "Get Started" or "Apply Now"
2. Fill registration form:
   - Email: frontend-test@example.com
   - Password: Test123!@#
   - Full Name: Frontend Test User
   - Phone: +919876543210
3. Click "Register"
4. **Expected:** Redirect to application page

### Test 3: Multi-Step Application
1. **Step 1: Category Selection**
   - Select "Gig Worker" card
   - Click "Next"
   
2. **Step 2: Personal Details**
   - Fill all required fields
   - Click "Next"
   
3. **Step 3: Category-Specific Data**
   - Platform: Uber
   - Tenure: 24 months
   - Monthly Earnings: ₹35,000
   - Monthly Trips: 450
   - Rating: 4.7
   - Click "Next"
   
4. **Step 4: Loan Details**
   - Amount: ₹50,000
   - Tenure: 12 months
   - Purpose: Vehicle purchase
   - Click "Submit Application"

5. **Expected:** Redirect to result page with credit score gauge

### Test 4: Result Page Components
**Verify all components render:**
- [ ] Credit Score Gauge (animated 300-850)
- [ ] Score Breakdown Card (5 pillars)
- [ ] Loan Terms Card (approval/rejection)
- [ ] SHAP Chart (positive/negative factors)
- [ ] What-If Simulator (sliders)
- [ ] Chatbot Widget (bottom-right)

### Test 5: What-If Simulator
1. Adjust income slider (+20%)
2. Adjust loan amount (₹60,000)
3. Click "Simulate"
4. **Expected:** Updated score and terms in real-time

### Test 6: Chatbot
1. Click chatbot icon (bottom-right)
2. Type: "Explain my score"
3. **Expected:** AI response explaining credit score factors

**✅ Pass Criteria:** All pages load, forms submit successfully, components render, animations work

---

## Phase 4: Admin Portal Test (10 minutes)

### Test 1: Create Admin User
```bash
# Connect to database
docker exec -it barclays_postgres psql -U admin -d barclays_credit

# Update user role
UPDATE users SET role = 'admin' WHERE email = 'test@example.com';
\q
```

### Test 2: Access Admin Portal
1. Login with admin credentials
2. Navigate to: http://localhost:3000/admin
3. **Expected:** Admin dashboard with KPIs

### Test 3: Dashboard Page
**Verify components:**
- [ ] Total Applications KPI
- [ ] Approval Rate KPI
- [ ] Average Credit Score KPI
- [ ] Applications by Risk chart
- [ ] Score Distribution chart
- [ ] Applications Trend chart

### Test 4: Pipeline Page
1. Navigate to: http://localhost:3000/admin/pipeline
2. **Expected:** Application table with filters
3. Click on an application row
4. **Expected:** Side panel opens with details

### Test 5: Fairness Page
1. Navigate to: http://localhost:3000/admin/fairness
2. **Expected:** DIR scores, bias flags, approval rates by group

### Test 6: Audit Log Page
1. Navigate to: http://localhost:3000/admin/audit
2. **Expected:** Timeline of events with filters
3. Click on an event
4. **Expected:** Modal with full event details

### Test 7: Model Registry Page
1. Navigate to: http://localhost:3000/admin/models
2. **Expected:** List of model versions with metrics

### Test 8: Portfolio Page
1. Navigate to: http://localhost:3000/admin/portfolio
2. **Expected:** Risk metrics, loss distribution chart, stress tests

**✅ Pass Criteria:** All admin pages load, charts render, data displays correctly

---

## Phase 5: ML Pipeline Test (5 minutes)

### Test 1: Score Preview (Direct ML Test)
```bash
curl -X POST http://localhost:8000/api/v1/applications/score-preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_category": "farmer",
    "monthly_income": 15000,
    "land_size_acres": 5,
    "crop_type": "wheat",
    "irrigation_available": true,
    "requested_amount": 30000,
    "requested_tenure_months": 12
  }'
```

**Expected Response:**
```json
{
  "credit_score": 680,
  "probability_of_default": 0.25,
  "risk_band": "medium",
  "decision_status": "manual_review",
  "confidence_tier": "medium",
  "shap_explanation": {
    "base_value": 0.35,
    "top_positive_factors": [...],
    "top_negative_factors": [...]
  },
  "pillar_scores": {
    "income_stability": 15,
    "repayment_capacity": 18,
    "spending_data": 10,
    "profile_completeness": 7,
    "alternative_data": 12
  }
}
```

### Test 2: Go-Live Gate Check
```bash
curl -X GET http://localhost:8000/api/v1/applications/go-live-gate \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "publish_allowed": true,
  "core_segment_recall": 0.85,
  "model_version": "v4",
  "message": "All guardrails passed"
}
```

**✅ Pass Criteria:** ML model loads, predictions return valid scores, SHAP values present

---

## Phase 6: Integration Test (10 minutes)

### Test 1: Complete User Journey
1. Register new user (API or Frontend)
2. Submit application (Frontend)
3. View credit score (Frontend)
4. Use what-if simulator (Frontend)
5. Chat with assistant (Frontend)
6. Check audit log (Admin portal)

### Test 2: Multiple User Categories
Submit applications for all 6 categories:
- [ ] Farmer
- [ ] Daily Wage Worker
- [ ] Gig Worker
- [ ] MSME Owner
- [ ] Homemaker (with nominee)
- [ ] Low Income Salaried

### Test 3: Fraud Detection
Submit application with suspicious data:
```bash
curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
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
  }'
```

**Expected:** High fraud score, application rejected or held

### Test 4: Policy Engine
Submit application violating EMI ratio:
```bash
curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_category": "low_income_salaried",
    "requested_amount": 200000,
    "requested_tenure_months": 12,
    "loan_purpose": "Personal",
    "category_data": {
      "monthly_salary_net": 15000,
      "employment_type": "permanent",
      "company_name": "ABC Corp",
      "years_at_current_job": 2
    }
  }'
```

**Expected:** Policy check fails, application held for review

**✅ Pass Criteria:** All user journeys complete, fraud detection works, policy engine validates

---

## Phase 7: Performance Test (5 minutes)

### Test 1: Response Time
```bash
# Test API response time
time curl -X GET http://localhost:8000/health

# Should be < 100ms
```

### Test 2: ML Scoring Time
```bash
# Test scoring time
time curl -X POST http://localhost:8000/api/v1/applications/score-preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"user_category":"gig_worker","monthly_income":30000}'

# Should be < 2 seconds
```

### Test 3: Concurrent Requests
```bash
# Install Apache Bench (if not installed)
# brew install httpd (macOS)
# apt-get install apache2-utils (Ubuntu)

# Test 100 concurrent requests
ab -n 100 -c 10 http://localhost:8000/health
```

**Expected:** 
- Average response time < 500ms
- No failed requests
- Throughput > 50 req/sec

**✅ Pass Criteria:** Response times within limits, no errors under load

---

## Phase 8: Error Handling Test (5 minutes)

### Test 1: Invalid Credentials
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wrong@example.com",
    "password": "WrongPass123"
  }'
```

**Expected:** 401 Unauthorized

### Test 2: Missing Required Fields
```bash
curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_category": "gig_worker"
  }'
```

**Expected:** 422 Validation Error

### Test 3: Invalid Application ID
```bash
curl -X GET http://localhost:8000/api/v1/applications/invalid-uuid/score \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** 400 Bad Request

**✅ Pass Criteria:** All errors return appropriate status codes and messages

---

## Test Results Summary

### Infrastructure
- [ ] All 4 services running
- [ ] Health checks passing
- [ ] Database connected
- [ ] Redis connected

### Backend API
- [ ] User registration works
- [ ] User login works
- [ ] Application submission works
- [ ] Credit scoring works
- [ ] What-if simulator works
- [ ] ML model loads and predicts

### Frontend
- [ ] Landing page loads
- [ ] Registration form works
- [ ] Multi-step application works
- [ ] Result page displays score
- [ ] All components render
- [ ] Chatbot responds

### Admin Portal
- [ ] Dashboard loads with KPIs
- [ ] Pipeline page shows applications
- [ ] Fairness monitoring works
- [ ] Audit log displays events
- [ ] Model registry shows versions
- [ ] Portfolio analytics display

### ML Pipeline
- [ ] Model loads successfully
- [ ] Predictions return valid scores
- [ ] SHAP values calculated
- [ ] Fraud detection works
- [ ] Policy engine validates

### Integration
- [ ] Complete user journey works
- [ ] All 6 user categories work
- [ ] Fraud detection triggers
- [ ] Policy violations caught

### Performance
- [ ] API response < 500ms
- [ ] ML scoring < 2 seconds
- [ ] Handles concurrent requests

### Error Handling
- [ ] Invalid credentials rejected
- [ ] Validation errors caught
- [ ] Invalid IDs handled

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Restart services
docker-compose restart
```

### Database Connection Error
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Recreate database
docker-compose down -v
docker-compose up -d db
```

### Frontend Build Error
```bash
# Clear cache and rebuild
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d
```

### ML Model Not Found
```bash
# Check model files exist
ls -la ml_pipeline/models/

# If missing, the system will run in degraded mode
# Check backend logs for warnings
```

---

## Success Criteria

**✅ PASS:** All tests pass, no critical errors  
**⚠️ PARTIAL:** Some tests pass, minor issues  
**❌ FAIL:** Critical tests fail, system not functional

---

## Next Steps After Testing

1. **If all tests pass:**
   - Document any issues found
   - Proceed with production deployment
   - Set up monitoring

2. **If tests fail:**
   - Check logs: `docker-compose logs`
   - Review error messages
   - Fix issues and re-test

3. **Performance issues:**
   - Check resource usage: `docker stats`
   - Optimize database queries
   - Add caching

---

**🎯 Goal: All tests passing = Production-ready system!**
