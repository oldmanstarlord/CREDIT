# Getting Started - Development Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ (with npm)
- Docker & Docker Compose
- Git
- PostgreSQL client (psql) - optional but useful
- Postman or curl for API testing

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd barclays-credit-platform
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local configuration
# For development, defaults should mostly work
nano .env
```

Key development settings:
```
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql://admin:postgres@localhost:5432/barclays_credit
JWT_SECRET=dev-secret-key  # Change for production!
```

### 3. Start Services with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

This will start:
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Backend API**: `http://localhost:8000`
- **Frontend React**: `http://localhost:3000`

### 4. Initialize Database

```bash
# Apply migrations (create tables)
docker-compose exec backend alembic upgrade head

# Load sample data (optional)
docker-compose exec backend python -m app.scripts.load_sample_data
```

### 5. Test the Installation

**API Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Frontend:**
- User Portal: http://localhost:3000
- Admin Portal: http://localhost:3000/admin

## Backend Development

### Project Structure

```
backend/
├── app/
│   ├── api/routes/              # API endpoints
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── applications.py       # Loan application endpoints
│   │   ├── scoring.py            # ML scoring endpoints
│   │   ├── admin.py             # Admin/risk management endpoints
│   │   ├── analytics.py         # Dashboard/reporting endpoints
│   │   └── ...
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── models.py            # All database tables
│   │   └── ...
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py          # All schemas defined here
│   ├── services/                # Business logic services/
│   │   ├── fraud_service.py      # Fraud detection
│   │   ├── policy_engine.py      # Policy rule enforcement
│   │   ├── trust_service.py      # Nominee/endorser framework
│   │   ├── genai_service.py      # OpenAI integration
│   │   ├── portfolio_service.py  # Portfolio risk analysis
│   │   └── ...
│   ├── ml/                      # ML pipeline
│   │   ├── feature_engineering.py # Feature extraction
│   │   ├── train.py              # Model training
│   │   ├── predict.py            # Inference/scoring
│   │   ├── explainability.py     # SHAP explanations
│   │   └── fairness.py           # Fairness monitoring
│   ├── core/                    # Core utilities
│   │   ├── config.py            # Configuration/constants
│   │   ├── security.py          # JWT/password utilities
│   │   └── logging.py           # Structured logging
│   ├── main.py                  # FastAPI application
│   └── ...
├── tests/                       # Pytest test suite
│   ├── test_fraud_service.py
│   ├── test_scoring_service.py
│   ├── test_api_auth.py
│   └── ...
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Backend container
└── ...
```

### Running Backend Tests

```bash
# All tests
docker-compose exec backend pytest

# Specific test file
docker-compose exec backend pytest tests/test_fraud_service.py

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Verbose output
docker-compose exec backend pytest -vv
```

### Backend Code Style

**Linting:**
```bash
# Install locally (optional)
pip install flake8 black

# Format code
black backend/app

# Lint
flake8 backend/app
```

**Requirements:**
- All functions must have docstrings
- Use type hints on all function signatures
- Max 80 characters per line (soft limit 100)
- No magic numbers - use config constants

### Adding New Endpoints

1. Create route function in `app/api/routes/<domain>.py`
2. Define Pydantic schemas in `app/schemas/__init__.py`
3. Add business logic in `app/services/<service>.py`
4. Write unit tests in `tests/test_<feature>.py`
5. Update API documentation

Example:
```python
# app/api/routes/applications.py

@router.post("/submit", response_model=LoanApplicationResponse)
async def submit_application(
    request: ApplicationSubmitRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Submit new loan application. Full docstring required."""
    # Implementation
    return response
```

### Working with Database

**Connect to PostgreSQL:**
```bash
# Using Docker
docker-compose exec db psql -U admin -d barclays_credit

# Or from host (if psql installed)
psql -h localhost -U admin -d barclays_credit
```

**Create Migration:**
```bash
docker-compose exec backend alembic revision --autogenerate -m "Add new column"
docker-compose exec backend alembic upgrade head
```

**View Tables:**
```bash
# In psql shell
\dt                    # List all tables
\d loan_applications   # Describe specific table
SELECT COUNT(*) FROM loan_applications;
```

## Frontend Development

### Project Structure

```
frontend/src/
├── pages/
│   ├── user/
│   │   ├── Onboarding.tsx       # Multi-step form
│   │   ├── CreditScore.tsx       # Score display
│   │   ├── WhatIfSimulator.tsx   # Interactive simulator
│   │   └── Dashboard.tsx         # User dashboard
│   ├── admin/
│   │   ├── ApplicationList.tsx    # Filterable app list
│   │   ├── ApplicationDetail.tsx # Deep dive view
│   │   ├── Dashboard.tsx        # KPI/charts dashboard
│   │   └── Analytics.tsx        # Reporting
│   └── Auth.tsx              # Login/register
├── components/
│   ├── CreditScoreGauge.tsx     # Animated dial
│   ├── ShapChart.tsx            # Feature importance
│   ├── ApplicationTable.tsx      # Data table
│   ├── ChatWidget.tsx           # Chatbot sidebar
│   └── ...
├── store/
│   ├── slices/
│   │   ├── authSlice.ts
│   │   ├── applicationSlice.ts
│   │   └── ...
│   └── store.ts                 # Redux store config
├── services/
│   ├── api.ts                   # API client
│   ├── auth.ts                  # Auth service
│   └── ...
├── utils/
│   ├── formatting.ts            # Format numbers/dates
│   ├── validation.ts            # Form validation
│   └── ...
├── App.tsx                      # Main app component
├── index.tsx                    # React entry point
└── index.css                    # Tailwind imports
```

### Running Frontend

**Development Mode:**
```bash
# Already running in docker-compose
# Or locally:
cd frontend
npm install
npm start
```

**Build for Production:**
```bash
npm run build
```

### Frontend Testing

```bash
# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Tailwind CSS

Configuration is in `frontend/tailwind.config.js`. Update there for custom:
- Colors
- Fonts
- Breakpoints
- Spacing

## ML Pipeline Development

### Feature Engineering

Edit `backend/app/ml/feature_engineering.py`:

```python
def engineer_farmer_features(self, data: Dict) -> Dict[str, float]:
    """Add new farmer features here"""
    features = {}
    # Your feature engineering logic
    return features
```

### Model Training

```bash
# From backend container
docker-compose exec backend python

# Then in Python REPL:
from app.ml.train import ModelTrainer
from app.schemas import receive sample data...

trainer = ModelTrainer()
trainer.train(X_train, y_train, X_val, y_val)
trainer.evaluate(X_test, y_test)
trainer.save("models/credit_scorer_v1.pkl")
```

### Monitoring Model Performance

Check logs for:
```
Model loaded successfully | AUC: 0.85 | Precision: 0.78 | Recall: 0.81
```

## Debugging

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f db

# All services
docker-compose logs -f
```

### Access Database

```bash
docker-compose exec db psql -U admin -d barclays_credit
```

### API Testing

**Using curl:**
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","phone_number":"9876543210","password":"secure","full_name":"John Doe"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure"}'

# Submit application (with token from login)
curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{...application data...}'
```

**Using Postman:**
1. Import OpenAPI spec from: http://localhost:8000/openapi.json
2. Set environment variable: `api_url = http://localhost:8000`
3. Set auth token in Authorization tab after login request

### Common Issues

**Port Already in Use:**
```bash
# Kill process on port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # Database
```

**Database Connection Error:**
```bash
# Check database is running
docker-compose logs db

# Reset database
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
```

**Module Import Errors:**
```bash
# Rebuild backend image
docker-compose build --no-cache backend
docker-compose up backend
```

## Deployment Preparation

### Environment Configuration

Update `.env` for production:
```
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=<production-db-url>
JWT_SECRET=<very-long-random-string>

### 2b. Dataset Setup (Required for ML)

Datasets must live in the workspace-level `datasets/` folder (one level above this project):

```bash
../datasets/raw/my-transaction/MyTransaction.csv
../datasets/raw/paysim-fraud/PS_20174392719_1491204439457_log.csv
../datasets/raw/give-me-some-credit/cs-training.csv
../datasets/raw/home-credit/application_train.csv
../datasets/raw/lending-club/loan.csv
```

Path configuration is managed via `.env` keys:

```bash
DATASETS_ROOT=../datasets
DATASETS_RAW_DIR=../datasets/raw
DATASETS_ARCHIVES_DIR=../datasets/archives
```

You can validate the configured layout quickly:

```bash
python - <<'PY'
from app.ml.dataset_paths import validate_dataset_layout
print(validate_dataset_layout())
PY
```
OPENAI_API_KEY=<production-key>
AWS_ACCESS_KEY_ID=<production-creds>
AWS_SECRET_ACCESS_KEY=<production-creds>
```

### Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### Build Docker Images

```bash
docker build -t barclays-credit:v1.0 ./backend
docker build -t barclays-credit-web:v1.0 ./frontend
```

### Health Checks

```bash
# Test API
curl http://localhost:8000/api/v1/health

# Test Database
docker-compose exec db pg_isready

# Test Redis
docker-compose exec redis redis-cli ping
```

---

**Need Help?**
- Check logs: `docker-compose logs -f <service>`
- Review relevant docstrings in code
- Check API docs: http://localhost:8000/docs
- Consult README.md for architecture overview
