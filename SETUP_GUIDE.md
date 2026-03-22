# Barclays Credit Intelligence Platform - Complete Setup Guide

## Overview
Production-grade AI-powered credit scoring system for unbanked populations in India. Serves farmers, gig workers, daily wage workers, MSME owners, homemakers, and low-income salaried workers.

## Prerequisites

### Required Software
- **Python 3.10+** (for backend)
- **Node.js 18+** and npm (for frontend)
- **PostgreSQL 15+** (database)
- **Redis 7+** (caching)
- **Docker & Docker Compose** (recommended for easy setup)

### Optional
- **AWS Account** (for S3 document storage - can run without)
- **OpenRouter API Key** (for chatbot - free tier available)

## Quick Start with Docker (Recommended)

### 1. Clone and Setup Environment

```bash
cd barclays-credit-platform
cp .env.example .env
# Edit .env with your configuration (see Configuration section below)
```

### 2. Start All Services

```bash
docker-compose up --build
```

This will start:
- PostgreSQL database on port 5432
- Redis cache on port 6379
- Backend API on port 8000
- Frontend React app on port 3000

### 3. Access the Application

- **User Portal**: http://localhost:3000
- **Admin Portal**: http://localhost:3000/admin
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## Manual Setup (Without Docker)

### 1. Database Setup

```bash
# Install PostgreSQL
# Create database
createdb barclays_credit

# Or using psql
psql -U postgres
CREATE DATABASE barclays_credit;
CREATE USER admin WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE barclays_credit TO admin;
\q
```

### 2. Redis Setup

```bash
# Install Redis
# Start Redis server
redis-server
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Configuration

### Essential Environment Variables

Edit `.env` file with these critical settings:

```bash
# Database
DATABASE_URL=postgresql://admin:postgres@localhost:5432/barclays_credit

# Security (CHANGE IN PRODUCTION!)
JWT_SECRET=your-super-secret-key-min-32-characters

# LLM Provider (Optional - for chatbot)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-key  # Get free key at openrouter.ai

# Or use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

### Getting API Keys

**OpenRouter (Recommended - Free Tier)**:
1. Visit https://openrouter.ai
2. Sign up for free account
3. Get API key from dashboard
4. Free models available: llama-3.1-8b-instruct, gpt-oss-20b

**OpenAI (Optional)**:
1. Visit https://platform.openai.com
2. Create account and add payment method
3. Generate API key
4. Use gpt-4o-mini for cost-effective option

## ML Model Setup

### Option 1: Use Pre-trained Model (Recommended)

The application expects a trained model at:
```
ml_pipeline/models/integration_contracts/winner_upgrade_v4/winner_v4_serving_artifact.pkl
```

If you don't have a trained model, the backend will start in degraded mode (scoring disabled).

### Option 2: Train Your Own Model

```bash
cd ml_pipeline

# Ensure datasets are in place (see Dataset Setup below)

# Run training pipeline
python run_training.py

# This will:
# 1. Load and clean datasets
# 2. Engineer features
# 3. Train XGBoost with Optuna HPO
# 4. Generate SHAP explainer
# 5. Save model artifact
```

## Dataset Setup

Place training datasets in `../datasets/raw/`:

```
datasets/
├── raw/
│   ├── give-me-some-credit/
│   │   ├── cs-training.csv
│   │   └── cs-test.csv
│   ├── home-credit/
│   │   ├── application_train.csv
│   │   └── application_test.csv
│   └── my-transaction/
│       └── MyTransaction.csv
```

**Dataset Sources**:
- Give Me Some Credit: https://www.kaggle.com/c/GiveMeSomeCredit
- Home Credit: https://www.kaggle.com/c/home-credit-default-risk
- Alternative data: Custom transaction logs

## Testing the Application

### 1. Create Test User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phone_number": "9876543210",
    "password": "testpass123",
    "full_name": "Test User",
    "user_category": "low_income_salaried"
  }'
```

### 2. Submit Test Application

Use the frontend at http://localhost:3000/apply or via API:

```bash
curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @test_application.json
```

### 3. Check Application Status

```bash
curl http://localhost:8000/api/v1/applications/{application_id}/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Admin Portal Access

### Create Admin User

```sql
-- Connect to database
psql barclays_credit

-- Update user role to admin
UPDATE users 
SET role = 'admin' 
WHERE email = 'your-email@example.com';
```

Then login at http://localhost:3000/admin

## Production Deployment

### 1. Security Checklist

- [ ] Change JWT_SECRET to strong random value (min 32 characters)
- [ ] Set DEBUG=False
- [ ] Set ENVIRONMENT=production
- [ ] Use strong database password
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS for production domain only
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure backup strategy

### 2. Database Migrations

```bash
# Always backup before migrations
pg_dump barclays_credit > backup.sql

# Run migrations
alembic upgrade head
```

### 3. Performance Optimization

- Enable Redis caching
- Use connection pooling
- Set up CDN for frontend assets
- Configure Nginx reverse proxy
- Enable gzip compression

### 4. Monitoring

- Check `/api/v1/health` endpoint
- Monitor database connections
- Track ML model performance
- Review audit logs regularly
- Monitor fairness metrics weekly

## Troubleshooting

### Backend won't start

**Error**: "Database connection failed"
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
# Verify user has permissions
```

**Error**: "ML model not found"
```bash
# Model is optional for development
# Set SIMULATE_MODE=True in .env to bypass
# Or train a model (see ML Model Setup)
```

### Frontend won't connect to backend

**Error**: "Network Error" or CORS issues
```bash
# Check REACT_APP_API_URL in .env
# Should be http://localhost:8000 for development

# Verify backend is running
curl http://localhost:8000/api/v1/health
```

### Redis connection failed

```bash
# Redis is optional - backend will log warning but continue
# To fix: ensure Redis is running
redis-cli ping  # Should return PONG
```

### Database migration errors

```bash
# Reset database (CAUTION: deletes all data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate
dropdb barclays_credit
createdb barclays_credit
alembic upgrade head
```

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
flake8 app/
black app/

# Frontend linting
cd frontend
npm run lint
npm run format
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Architecture Overview

```
┌─────────────────┐
│  React Frontend │ :3000
│  (User Portal)  │
└────────┬────────┘
         │
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Backend│ :8000
│  (API Server)   │
└────────┬────────┘
         │
    ┌────┴────┬────────┬─────────┐
    ▼         ▼        ▼         ▼
┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Postgres│ │Redis │ │XGBoost│ │OpenAI│
│  :5432 │ │:6379 │ │ Model │ │ API  │
└────────┘ └──────┘ └──────┘ └──────┘
```

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Architecture**: See DEVELOPMENT.md
- **Data Dictionary**: See DATA_DICTIONARY.md
- **Release Checklist**: See RELEASE_CHECKLIST.md

## License

Proprietary - Barclays Bank PLC

## Contact

For issues or questions, contact the development team.
