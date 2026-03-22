# Project Structure

## Directory Overview

```
barclays-credit-platform/
├── backend/                    # FastAPI backend application
│   ├── alembic/               # Database migrations
│   │   └── versions/          # Migration files
│   ├── app/                   # Main application code
│   │   ├── api/              # API routes
│   │   │   └── routes/       # Route modules
│   │   ├── core/             # Core functionality
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic services
│   │   └── ml/               # ML pipeline
│   ├── tests/                # Backend tests
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Backend container
│   └── alembic.ini          # Alembic configuration
│
├── frontend/                  # React frontend application
│   ├── public/               # Static assets
│   ├── src/                  # Source code
│   │   ├── components/       # Reusable components
│   │   ├── pages/           # Page components
│   │   │   ├── admin/       # Admin portal pages
│   │   │   └── user/        # User portal pages
│   │   ├── services/        # API services
│   │   ├── store/           # Redux store
│   │   ├── App.tsx          # Main app component
│   │   └── index.tsx        # Entry point
│   ├── package.json         # Node dependencies
│   ├── Dockerfile          # Frontend container
│   └── nginx.conf          # Nginx configuration
│
├── ml_pipeline/              # ML training and models
│   ├── models/              # Trained model artifacts
│   │   └── integration_contracts/  # Production models
│   └── notebooks/           # Jupyter notebooks
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── DATA_DICTIONARY.md   # Database schema
│   ├── DEVELOPMENT.md       # Development guide
│   ├── TESTING_GUIDE.md     # Testing instructions
│   ├── TEST_PLAN.md         # Test strategy
│   └── PROJECT_STRUCTURE.md # This file
│
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
├── docker-compose.yml      # Docker orchestration
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
├── README.md              # Main documentation
├── SETUP_GUIDE.md         # Installation guide
├── start.sh               # Quick start script
└── run_tests.sh           # Test runner script
```

## Backend Structure

### `/backend/app/api/routes/`
API endpoint definitions organized by domain:
- `auth.py` - Authentication endpoints (login, register, refresh)
- `applications.py` - Loan application endpoints
- `admin.py` - Admin portal endpoints
- `chat.py` - Chatbot endpoints

### `/backend/app/core/`
Core infrastructure:
- `config.py` - Configuration management
- `database.py` - Database connection
- `security.py` - Authentication & authorization
- `logging.py` - Structured logging

### `/backend/app/models/`
SQLAlchemy ORM models:
- `models.py` - All database models (User, LoanApplication, etc.)

### `/backend/app/schemas/`
Pydantic schemas for request/response validation:
- `__init__.py` - All API schemas

### `/backend/app/services/`
Business logic services:
- `fraud_service.py` - Fraud detection engine
- `policy_engine.py` - Business rule validation
- `audit_service.py` - Audit trail logging
- `chatbot_service.py` - LLM integration
- `fairness_service.py` - Bias detection
- `portfolio_service.py` - Risk simulation
- `trust_service.py` - Nominee validation
- `aws_service.py` - S3 operations
- `notification_service.py` - Email/SMS

### `/backend/app/ml/`
ML pipeline:
- `feature_engineering.py` - Feature extraction (50+ features)
- `train.py` - Model training
- `predict.py` - Scoring service
- `dataset_paths.py` - Data locations

## Frontend Structure

### `/frontend/src/components/`
Reusable UI components (21 total):
- Form components (CategorySelector, DynamicFormRenderer)
- Display components (CreditScoreGauge, ScoreBreakdownCard)
- Interactive components (WhatIfSimulator, ChatbotWidget)
- Admin components (ApplicationTable, DecisionPanel)
- Analytics components (FairnessMonitor, PortfolioRiskView)

### `/frontend/src/pages/`
Page-level components:

**User Portal:**
- `PortalSelectionPage.tsx` - Landing page
- `user/LandingPage.tsx` - User login
- `user/ApplicationPage.tsx` - Loan application form
- `user/ResultPage.tsx` - Credit score results

**Admin Portal:**
- `AdminLoginPage.tsx` - Admin login
- `admin/DashboardPage.tsx` - KPI dashboard
- `admin/PipelinePage.tsx` - Application pipeline
- `admin/FairnessPage.tsx` - Fairness monitoring
- `admin/AuditLogPage.tsx` - Audit logs
- `admin/ModelRegistryPage.tsx` - ML model registry
- `admin/PortfolioPage.tsx` - Portfolio risk

### `/frontend/src/services/`
API client services:
- `api.ts` - Axios configuration
- `authService.ts` - Authentication API
- `applicationService.ts` - Application API
- `adminService.ts` - Admin API

### `/frontend/src/store/`
Redux state management:
- `store.ts` - Store configuration
- `authSlice.ts` - Auth state
- `applicationSlice.ts` - Application state
- `adminSlice.ts` - Admin state

## ML Pipeline Structure

### `/ml_pipeline/models/`
Trained model artifacts:
- `integration_contracts/winner_upgrade_v4/` - Production model (v4)
- `best_model_*.pkl` - Previous model versions
- Model metadata and manifests

### `/ml_pipeline/notebooks/`
Jupyter notebooks for:
- Data exploration
- Feature engineering
- Model training
- Performance analysis

## Configuration Files

### Root Level
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore patterns
- `docker-compose.yml` - Multi-container orchestration
- `start.sh` - Quick start script
- `run_tests.sh` - Test execution script

### Backend
- `requirements.txt` - Python dependencies
- `alembic.ini` - Database migration config
- `pytest.ini` - Test configuration
- `Dockerfile` - Backend container definition

### Frontend
- `package.json` - Node.js dependencies
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.js` - Tailwind CSS config
- `postcss.config.js` - PostCSS config
- `nginx.conf` - Web server config
- `Dockerfile` - Frontend container definition

## Key Files

### Documentation
- `README.md` - Main project documentation
- `SETUP_GUIDE.md` - Installation instructions
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - MIT License

### Scripts
- `start.sh` - Start all services
- `run_tests.sh` - Run test suite

## Data Flow

```
User Request
    ↓
Frontend (React)
    ↓ HTTP/REST
Backend API (FastAPI)
    ↓
Services Layer
    ├─→ Fraud Detection
    ├─→ ML Scoring
    ├─→ Policy Validation
    └─→ Audit Logging
    ↓
Data Layer
    ├─→ PostgreSQL (persistent data)
    ├─→ Redis (cache)
    └─→ S3 (documents)
```

## Module Dependencies

### Backend
```
FastAPI → SQLAlchemy → PostgreSQL
       → Redis
       → XGBoost/SHAP (ML)
       → Boto3 (AWS)
```

### Frontend
```
React → Redux Toolkit (state)
      → Axios (HTTP)
      → Recharts (visualization)
      → Tailwind CSS (styling)
```

## Environment-Specific Files

### Development
- `.env` (local configuration)
- `docker-compose.yml` (local services)

### Production
- `.env.production` (production config)
- `docker-compose.prod.yml` (production services)
- SSL certificates
- Monitoring configuration

## Testing Structure

### Backend Tests
```
backend/tests/
├── test_credit_scorer_contract.py
├── test_new_services.py
├── test_uuid_guards.py
└── test_winner_resolution.py
```

### Frontend Tests
```
frontend/src/
├── components/__tests__/
├── pages/__tests__/
└── services/__tests__/
```

## Build Artifacts

### Backend
- `__pycache__/` - Python bytecode
- `.pytest_cache/` - Test cache
- `*.egg-info/` - Package metadata

### Frontend
- `node_modules/` - Node dependencies
- `build/` - Production build
- `.next/` - Next.js cache (if using)

## Logs

### Application Logs
- Backend: Structured JSON logs to stdout
- Frontend: Browser console
- Nginx: Access and error logs

### Audit Logs
- Stored in PostgreSQL `audit_logs` table
- Immutable event records
- Includes all user actions

## Security

### Sensitive Files (Never Commit)
- `.env` - Environment variables
- `*.pem` - SSL certificates
- `*.key` - Private keys
- Credentials files

### Protected by .gitignore
- Environment files
- Credentials
- Build artifacts
- Cache directories
- Log files

## Deployment

### Docker Images
- `barclays_backend` - Backend service
- `barclays_frontend` - Frontend service
- `postgres:15-alpine` - Database
- `redis:7-alpine` - Cache

### Volumes
- `postgres_data` - Database persistence
- `./backend:/app` - Backend code (dev)
- `./frontend:/app` - Frontend code (dev)
- `./ml_pipeline/models:/app/models` - ML models

## Maintenance

### Regular Updates
- Python dependencies (`requirements.txt`)
- Node dependencies (`package.json`)
- Docker base images
- ML models

### Monitoring
- Application logs
- Database performance
- API response times
- Error rates

---

For more details, see:
- [Architecture Guide](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)
- [Setup Guide](../SETUP_GUIDE.md)
