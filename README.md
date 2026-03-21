# Barclays Credit Intelligence Platform

**Production-grade, AI-powered credit intelligence system for financial inclusion**

A comprehensive fintech platform designed to extend credit access to unbanked and underbanked populations - farmers, daily wage workers, gig workers, MSMEs, homemakers, and low-income salaried individuals - who lack traditional credit histories.

## 🎯 Mission

Enable Barclays to responsibly lend to credit-excluded populations by:
1. **Alternative Data**: Score using behavioral data, platform activity, and land/business information instead of credit history
2. **Explainability**: Every decision must be understandable and auditable
3. **Fairness**: Monitor for bias and ensure equitable access
4. **Regulatory Compliance**: Meet RBI Fair Practices Code, EU AI Act, and data protection requirements

## 🏗️ Architecture

### Technology Stack

```
Backend:        FastAPI (Python 3.10+)
Frontend:       React 18+ with TypeScript
Database:       PostgreSQL + Redis
ML Engine:      XGBoost + SHAP + scikit-learn
Deployment:     Docker + docker-compose
API Auth:       JWT with role-based access
Monitoring:     Structured JSON logging
```

### Key Components

```
barclays-credit-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API endpoints
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic services
│   │   │   ├── fraud_service.py
│   │   │   ├── policy_engine.py
│   │   │   ├── trust_service.py
│   │   │   └── ... (scoring, fairness, genai, etc.)
│   │   ├── ml/                  # ML pipeline
│   │   ├── core/                # Core config, security, logging
│   │   └── main.py              # FastAPI application
│   └── tests/                   # Pytest test suite
├── frontend/                    # React application
├── ml_pipeline/                 # ML model training and evaluation
└── docker-compose.yml           # Production orchestration
```

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+

### Quick Start

#### 1. Clone and Navigate

```bash
cd barclays-credit-platform
```

#### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Build and Start Services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Backend FastAPI** on port 8000
- **Frontend React** on port 3000

## 📁 Dataset Layout (Canonical)

All raw datasets are stored at workspace level under `../datasets`.
The application code under `barclays-credit-platform/` remains clean and code-only.

```
../datasets/
├── raw/
│   ├── my-transaction/
│   │   └── MyTransaction.csv
│   ├── paysim-fraud/
│   │   └── PS_20174392719_1491204439457_log.csv
│   ├── give-me-some-credit/
│   │   ├── cs-training.csv
│   │   ├── cs-test.csv
│   │   ├── sampleEntry.csv
│   │   └── Data Dictionary.xls
│   ├── home-credit/
│   │   ├── application_train.csv
│   │   ├── application_test.csv
│   │   ├── HomeCredit_columns_description.csv
│   │   ├── bureau.csv
│   │   ├── bureau_balance.csv
│   │   ├── credit_card_balance.csv
│   │   ├── installments_payments.csv
│   │   ├── POS_CASH_balance.csv
│   │   ├── previous_application.csv
│   │   └── sample_submission.csv
│   └── lending-club/
│       ├── loan.csv
│       └── LCDataDictionary.xlsx
└── archives/
  ├── give-me-some-credit.zip
  ├── home-credit-default-risk.zip
  ├── lending-club.zip
  └── paysim-fraud.zip
```

Dataset paths are configured in `.env` and loaded through:
- `backend/app/core/config.py`
- `backend/app/ml/dataset_paths.py`

#### 4. Initialize Database

```bash
docker-compose exec backend alembic upgrade head
```

#### 5. Access Applications

- **User Portal**: http://localhost:3000
- **Admin Portal**: http://localhost:3000/admin
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

## 📋 Core Features

### 👤 User-Facing Application (Borrower Portal)

#### 1. **Multi-Step Onboarding**
- Step 1: Personal identity details (Name, DOB, Aadhaar, Phone, Email)
- Step 2: User category selection (Farmer, Daily Wage, Gig Worker, MSME, Homemaker, Salaried)
- Step 3: Category-specific data collection (Dynamic forms per category)

#### 2. **Category-Specific Data Collection**

**Farmers:**
- Land details (size, location, crop, irrigation)
- Expected harvest season and income
- Kisan Credit Card information
- Land valuation via GenAI (supplementary signal)

**Daily Wage Workers:**
- Occupation and daily earnings
- Work consistency pattern
- UPI transaction history (optional, consented)
- Bank account status

**Gig Workers:**
- Platform(s) (Ola, Zomato, Uber, etc.)
- Weekly earnings and platform tenure
- Platform trust scoring (integrated_signals)

**MSME Owners:**
- Business type, age, revenue, expenses
- GST/Udyam registration details
- Bank statements and business growth trends

**Homemakers:**
- Household income and family information
- Spouse/guardian employment details
- **Requires nominee (trust framework)**

#### 3. **Credit Score Output Screen**
- Score: 300-850 band visualization
- Risk classification (Low/Medium/High/Very High)
- Probability of Default with confidence interval
- Loan recommendation (amount, tenure, rate, EMI)
- Score breakdown by 5 pillars
- SHAP feature importance (top factors)
- Plain-English explanation via GenAI

#### 4. **What-If Simulator**
- Interactive adjustment of loan parameters
- Real-time score and terms recalculation
- No database writes (ephemeral simulation)
- < 2 second response time

#### 5. **Trust Framework (Nominee System)**
- Optional nominee/endorser for risk reduction
- Nominee eligibility validation
- Collateral support and valuation
- Exposure caps based on nominee quality

#### 6. **GenAI Chatbot Assistant**
- Contextual help on credit score
- FAQ about loan process
- SHAP explanation translation to plain language
- Redirects to support when needed

### 🏢 Admin Portal (Barclays Risk Team)

#### 1. **Application Pipeline Dashboard**
- Intelligent queue management:
  - 🔴 **Urgent**: High fraud scores, 72+ hour holds
  - 🟡 **Hold Queue**: ML-scored, policy-held, needs review
  - 🟢 **Recommend Approve**: Auto-approved (pending sign-off)
  - ⚫ **Auto-Rejected**: Failed rules, available for appeal
  - 📊 **Bulk Candidates**: High-confidence rejections

#### 2. **Individual Application Deep-Dive**
- Full applicant profile (masked sensitive data)
- Complete fraud analysis with individual flag details
- ML scoring output with SHAP feature importance chart
- Policy engine results (which rules passed/failed)
- Trust framework assessment
- Recommended decision and loan terms
- Role-gated decision panel (approve/reject/hold/override)
- Complete audit trail of all actions

#### 3. **Analytics Dashboard**
**KPI Summary:**
- Applications (today/week/month)
- Approval rate
- Average credit score
- Average loan amount
- Portfolio at-risk percentage
- Fraud detection rate
- Processing time average

**Charts:**
- Application status trends (30-day rolling)
- Credit score distribution by category
- Approval/rejection rate by category
- PD distribution (risk concentration)
- Loan amount distribution
- Fraud score distribution
- Credit ladder tier progression
- Monthly EMI default rate
- Regional heatmap (application volume by state)
- SHAP global feature importance

#### 4. **Fairness Monitoring Module**
- Weekly disparate impact ratio analysis
- Subgroup performance metrics (AUC, precision, recall)
- Bias detection and severity flagging
- Automated alerts if four-fifths rule violated
- Management review workflow

#### 5. **Audit Log Viewer**
- Timestamped event timeline for each application
- Who did what and when (immutable records)
- Model version tracking per decision
- Override justifications
- Full audit trail for regulatory compliance

#### 6. **Model Registry & Version Management**
- All deployed model versions
- Training metrics (AUC, precision, recall, F1)
- Fairness metrics at training time
- Deployment and deprecation dates
- SHAP global importance archived per version

## 🧠 Machine Learning Pipeline

### Feature Engineering

**Standard Ratio Features:**
```python
- debt_to_income_ratio
- credit_utilization_ratio
- payment_to_income_ratio
- num_late_payments_ratio
- income_per_dependent
```

**Alternative Behavioral Features (key for unbanked):**
```python
- income_stability (variance of reported income)
- transaction_consistency (regularity of UPI/bank)
- utility_payment_score (bill payment regularity)
- savings_buffer_ratio (emergency fund capacity)
- spending_pattern_ratio (essential vs discretionary)
- cash_flow_volatility (income unpredictability)
```

**Category-Specific Features:**
```python
# Farmers
- land_value_proxy
- seasonal_income_flag
- harvest_income_multiplier

# Gig Workers
- platform_trust_score
- weekly_income_cv (income variability)

# MSME
- revenue_growth_trend
- profit_margin
- expense_to_revenue_ratio
```

### Model Training Strategy

1. **Baseline**: Logistic Regression with class_weight='balanced'
2. **ECE Analysis**: Random Forest for feature importance
3. **Primary**: XGBoost with Optuna hyperparameter optimization
4. **Imbalance Handling**: Compare SMOTE vs class_weight
5. **Threshold Tuning**: Optimize decision threshold for business cost function

### Explainability (SHAP)

Every decision includes:
- **Global SHAP**: How features rank across entire population
- **Local SHAP**: How this applicant's factors combine
- **Plain English Translation**: GenAI explanation of complex interactions

### Fairness Monitoring

**Protected Attributes (never in model, only post-hoc monitoring):**
- Gender, religion, caste, ethnicity, region

**Metrics:**
- Disparate Impact Ratio (four-fifths rule: ≥ 0.80)
- Subgroup AUC/precision/recall
- Weekly automated checks with alerts

## 🔐 Security & Compliance

### Authentication & Authorization

- **JWT tokens** with customizable expiration
- **Role-based access control**:
  - `borrower`: Can access own application only
  - `analyst`: Can view and annotate applications
  - `senior_analyst`: Can recommend decisions
  - `risk_manager`: Can approve/reject with override capability
  - `admin`: Full system access

### Regulatory Compliance

**Implemented:**
```
✅ No protected attributes in model training
✅ Explainability for every decision (SHAP + GenAI)
✅ Immutable audit log for all actions
✅ Right to explanation (user-visible)
✅ Fairness monitoring (weekly disparate impact checks)
✅ Data minimization (only necessary fields)
✅ Override documentation (mandatory text field)
✅ Model version tracking per decision
✅ Processing delays for regulatory review when needed
```

### Data Protection

- PostgreSQL with encryption at rest
- JWT + HTTPS for transit security
- Document storage in S3 with versioning
- Automatic audit log export for compliance

## 📊 Database Schema

### Core Tables

**users**: Borrower and admin accounts
**loan_applications**: Application lifecycle tracking
**category_specific_data**: Flexible category-specific fields (JSON)
**nominees**: Endorser/trust framework information
**documents**: Document metadata (files in S3)
**decisions**: Final credit decisions with terms
**shap_explanation**: Per-application feature importance
**audit_logs**: Immutable event trail (no deletes/updates)
**fairness_metrics**: Weekly bias monitoring results
**model_versions**: ML model registry

## 🔄 Application Processing Pipeline

### Stage 1: Pre-Screening (Automated, <100ms)
```
Identity Validity      → Aadhaar format, phone format, email format
Minimum Income Threshold → Category-specific minimums
Basic Stability Signals → Bank account or UPI or document proof
Fraud Check            → Composite rule-based fraud score

Decision: PASS / HOLD / REJECT
```

### Stage 2: ML Scoring (Model inference)
```
Feature Engineering    → Extract 50+ features
XGBoost Prediction     → Probability of Default (0-1)
SHAP Explanation       → Feature importance per applicant
Trust Adjustment       → Adjust PD based on nominee quality
Credit Score           → Convert PD to 300-850 scale

Output: PD, Credit Score, Risk Band, SHAP explanation
```

### Stage 3: Policy Engine (Hard Rules)
```
EMI Affordability      → EMI ≤ 30-40% of monthly income (category-dependent)
Risk Threshold         → PD > 65% = auto-reject, PD < 15% = auto-approve
Credit Score Minimum   → ≥ 500 for any approval
Exposure Caps          → Per-user total ≤ ₹10,00,000
New User Cap           → First loan ≤ ₹50,000
Collateral Requirement → Loans > ₹1,00,000 need collateral or nominee

Decision: APPROVE / HOLD / REJECT
```

### Stage 4: Human Review (Analyst/Risk Manager)

- **Analyst**: Views application, reviews model reasoning, adds notes
- **Senior Analyst**: Can recommend decisions
- **Risk Manager**: Makes final approval/rejection with optional override
- **All actions logged with timestamp and justification**

## 💰 Loan Product Framework

### Credit Ladder (Progressive Access)

**Tier 0 - New User** (0-6 months)
- Max loan: ₹50,000
- Interest: 18-25%
- No collateral required
- Micro personal loan only

**Tier 1 - Trust Building** (6-18 months, clean repayment)
- Max loan: ₹5,00,000
- Interest: 12-18%
- Personal + business loans

**Tier 2 - Established** (18-36 months)
- Max loan: ₹10,00,000
- Interest: 10-14%
- Large loans, vehicle loans

**Tier 3 - Prime** (2-3+ years)
- Unlimited (score-based)
- Interest: 8-10%
- Home loans, secured loans

### Interest Rate Matrix

```
Small (≤ ₹1L):                    18-25%
Medium (₹1-3L):                   12-18%
Large (₹3-10L):                   10-12%
Premium (> ₹10L):                 8-10%
```

Rates also depend on tenure (shorter = higher rate).

### Repayment Terms

**Monthly EMI:**
- Minimum direct debit from account
- Late payment penalties: Day 7+ onwards
- Default definition: 90+ days

**Seasonal/Alternative Repayment:**
- Farmers: Harvest-time repayment (no monthly EMI)
- Gig workers: Flexible partial quarterly payments
- MSMEs: Revenue-linked repayment option

## 🛠️ API Endpoints

### Authentication
```
POST   /api/v1/auth/register         Register new user
POST   /api/v1/auth/login            Login and get tokens
POST   /api/v1/auth/refresh          Refresh access token
POST   /api/v1/auth/logout           Invalidate session
GET    /api/v1/auth/me               Current user profile
```

### Applications (User-Facing)
```
POST   /api/v1/applications/submit                 Submit application
GET    /api/v1/applications/{id}/status            Get processing status
GET    /api/v1/applications/{id}/score             Get credit score result
POST   /api/v1/applications/{id}/simulate          What-if simulator
POST   /api/v1/applications/{id}/documents/upload  Upload document
POST   /api/v1/applications/{id}/appeal            Appeal rejection
```

### Scoring (Internal)
```
POST   /api/v1/scoring/score                       Run ML scoring
GET    /api/v1/scoring/shap/{application_id}      Get SHAP explanation
```

### Admin
```
GET    /api/v1/admin/applications                  Filtered application list
GET    /api/v1/admin/applications/{id}             Full application detail
PUT    /api/v1/admin/applications/{id}/decide      Make decision
POST   /api/v1/admin/applications/{id}/override    Override model decision
GET    /api/v1/admin/dashboard/kpis                KPI summary
GET    /api/v1/admin/dashboard/charts/{type}       Chart data
GET    /api/v1/admin/fairness/report               Weekly fairness analysis
GET    /api/v1/admin/audit/logs                    Audit event timeline
GET    /api/v1/admin/models                        Model registry
POST   /api/v1/admin/models/deploy/{version}      Activate model version
```

## 🧪 Testing

### Backend (Pytest)

```bash
# Run all tests
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app

# Specific test file
docker-compose exec backend pytest tests/test_fraud_service.py
```

### Frontend (Jest)

```bash
cd frontend
npm test
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Schema**: http://localhost:8000/openapi.json
- **Architecture**: See `/docs/ARCHITECTURE.md`
- **Data Dictionary**: See `/docs/DATA_DICTIONARY.md`
- **ML Model Docs**: See `/ml_pipeline/README.md`

## 🚢 Deployment

### Production Deployment

```bash
# Build and push Docker images
docker build -t barclays-credit:v1.0 ./backend
docker build -t barclays-credit-web:v1.0 ./frontend

# Deploy with docker-compose
docker-compose -f docker-compose.yml up -d
```

### Environment Variables

```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/barclays
JWT_SECRET=<very-long-random-string>
OPENAI_API_KEY=<your-api-key>
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
```

## 📈 Monitoring & Logging

### Structured Logging

All logs are JSON-formatted for easy parsing by CloudWatch/ELK:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Application submitted",
  "user_id": "user-123",
  "application_id": "app-456",
  "category": "gig_worker",
  "requested_amount": 50000
}
```

### Key Metrics to Monitor

- Application submission rate (per category)
- Pre-screening fraud detection rate
- ML scoring latency (p50, p95, p99)
- Approval rate by category
- Portfolio at-risk percentage
- Credit score distribution
- Fairness metrics (disparate impact ratios)
- Model inference errors

## 🤝 Contributing

### Code Style

- Python: PEP 8, type hints on all functions
- React: ESLint + Prettier
- Database: Follow naming conventions in migrations
- Commits: Descriptive messages, separate concerns

### Pull Request Process

1. Create feature branch
2. Implement with tests
3. Ensure all checks pass
4. Request review from relevant domain experts
5. Squash and merge to main

## 📝 License

Confidential - Barclays Internal Use Only

## 📞 Support

**For technical issues:**
- Create issue in Jira with detailed reproduction steps
- Tag relevant team (ML, backend, frontend, DevOps)

**For business questions:**
- Contact Credit Risk team
-Contact Regulatory Compliance team

---

**Last Updated**: March 2024  
**Maintained By**: Barclays Credit Intelligence Team
