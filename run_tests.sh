#!/bin/bash

# Barclays Credit Platform - Automated Test Script
# This script tests the entire platform end-to-end

set -e  # Exit on error

echo "🧪 Barclays Credit Platform - Automated Test Suite"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
API_URL="http://localhost:8000/api/v1"
FRONTEND_URL="http://localhost:3000"

# Test counters
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

info() {
    echo -e "ℹ INFO: $1"
}

# Wait for services
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    info "Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            pass "$name is ready"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    fail "$name failed to start after $max_attempts attempts"
    return 1
}

echo "📋 Phase 1: Infrastructure Tests"
echo "================================"
echo ""

# Test 1: Check if services are running
info "Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    pass "Docker services are running"
else
    fail "Docker services are not running"
    echo "Please run: docker-compose up -d"
    exit 1
fi

# Test 2: Wait for backend
wait_for_service "http://localhost:8000/health" "Backend API"

# Test 3: Wait for frontend
wait_for_service "http://localhost:3000" "Frontend"

# Test 4: Health checks
echo ""
info "Running health checks..."

# Backend health
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    pass "Backend health check"
else
    fail "Backend health check"
fi

# Database health
if curl -s http://localhost:8000/health/db | grep -q "connected"; then
    pass "Database health check"
else
    fail "Database health check"
fi

# Redis health
if curl -s http://localhost:8000/health/redis | grep -q "connected"; then
    pass "Redis health check"
else
    fail "Redis health check"
fi

echo ""
echo "📋 Phase 2: Backend API Tests"
echo "=============================="
echo ""

# Test 5: User Registration
info "Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-'$(date +%s)'@example.com",
    "password": "Test123!@#",
    "full_name": "Test User",
    "phone_number": "+919876543210"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "user_id"; then
    pass "User registration"
    TEST_EMAIL=$(echo "$REGISTER_RESPONSE" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
else
    fail "User registration"
    echo "Response: $REGISTER_RESPONSE"
fi

# Test 6: User Login
info "Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'$TEST_EMAIL'",
    "password": "Test123!@#"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    pass "User login"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
else
    fail "User login"
    echo "Response: $LOGIN_RESPONSE"
fi

# Test 7: Submit Application
info "Testing loan application submission..."
APP_RESPONSE=$(curl -s -X POST "$API_URL/applications/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
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
  }')

if echo "$APP_RESPONSE" | grep -q "application_id"; then
    pass "Application submission"
    APPLICATION_ID=$(echo "$APP_RESPONSE" | grep -o '"application_id":"[^"]*"' | cut -d'"' -f4)
    info "Application ID: $APPLICATION_ID"
else
    fail "Application submission"
    echo "Response: $APP_RESPONSE"
fi

# Test 8: Get Credit Score
if [ ! -z "$APPLICATION_ID" ]; then
    info "Testing credit score retrieval..."
    sleep 2  # Wait for ML processing
    SCORE_RESPONSE=$(curl -s -X GET "$API_URL/applications/$APPLICATION_ID/score" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$SCORE_RESPONSE" | grep -q "credit_score"; then
        pass "Credit score retrieval"
        CREDIT_SCORE=$(echo "$SCORE_RESPONSE" | grep -o '"credit_score":[0-9]*' | cut -d':' -f2)
        info "Credit Score: $CREDIT_SCORE"
        
        # Validate score range
        if [ "$CREDIT_SCORE" -ge 300 ] && [ "$CREDIT_SCORE" -le 850 ]; then
            pass "Credit score in valid range (300-850)"
        else
            fail "Credit score out of range: $CREDIT_SCORE"
        fi
    else
        fail "Credit score retrieval"
        echo "Response: $SCORE_RESPONSE"
    fi
fi

# Test 9: What-If Simulator
if [ ! -z "$APPLICATION_ID" ]; then
    info "Testing what-if simulator..."
    SIM_RESPONSE=$(curl -s -X POST "$API_URL/applications/$APPLICATION_ID/simulate" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d '{
        "adjusted_income_percentage": 20,
        "adjusted_loan_amount": 60000,
        "adjusted_tenure_months": 18
      }')

    if echo "$SIM_RESPONSE" | grep -q "adjusted_credit_score"; then
        pass "What-if simulator"
    else
        fail "What-if simulator"
        echo "Response: $SIM_RESPONSE"
    fi
fi

# Test 10: Score Preview (Direct ML Test)
info "Testing ML model directly..."
ML_RESPONSE=$(curl -s -X POST "$API_URL/applications/score-preview" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "user_category": "farmer",
    "monthly_income": 15000,
    "land_size_acres": 5,
    "crop_type": "wheat",
    "irrigation_available": true,
    "requested_amount": 30000,
    "requested_tenure_months": 12
  }')

if echo "$ML_RESPONSE" | grep -q "credit_score"; then
    pass "ML model prediction"
    if echo "$ML_RESPONSE" | grep -q "shap_explanation"; then
        pass "SHAP explainability"
    else
        warn "SHAP values not found in response"
    fi
else
    fail "ML model prediction"
    echo "Response: $ML_RESPONSE"
fi

echo ""
echo "📋 Phase 3: Frontend Tests"
echo "=========================="
echo ""

# Test 11: Frontend accessibility
info "Testing frontend pages..."
if curl -s "$FRONTEND_URL" | grep -q "Barclays\|Credit\|Loan"; then
    pass "Frontend landing page loads"
else
    fail "Frontend landing page loads"
fi

# Test 12: API documentation
info "Testing API documentation..."
if curl -s "http://localhost:8000/docs" | grep -q "swagger\|openapi"; then
    pass "API documentation accessible"
else
    fail "API documentation accessible"
fi

echo ""
echo "📋 Phase 4: Error Handling Tests"
echo "================================"
echo ""

# Test 13: Invalid credentials
info "Testing invalid login..."
INVALID_LOGIN=$(curl -s -w "%{http_code}" -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wrong@example.com",
    "password": "WrongPass123"
  }')

if echo "$INVALID_LOGIN" | grep -q "401"; then
    pass "Invalid credentials rejected (401)"
else
    fail "Invalid credentials should return 401"
fi

# Test 14: Missing required fields
info "Testing validation..."
VALIDATION_TEST=$(curl -s -w "%{http_code}" -X POST "$API_URL/applications/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "user_category": "gig_worker"
  }')

if echo "$VALIDATION_TEST" | grep -q "422"; then
    pass "Validation errors caught (422)"
else
    fail "Validation should return 422"
fi

echo ""
echo "=================================================="
echo "📊 Test Results Summary"
echo "=================================================="
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! System is working correctly.${NC}"
    echo ""
    echo "✅ Next steps:"
    echo "  1. Access frontend: $FRONTEND_URL"
    echo "  2. Access API docs: http://localhost:8000/docs"
    echo "  3. Test manually using the web interface"
    echo "  4. Review TEST_PLAN.md for detailed testing"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the logs above.${NC}"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "  1. Check logs: docker-compose logs backend"
    echo "  2. Check database: docker-compose logs db"
    echo "  3. Restart services: docker-compose restart"
    exit 1
fi
