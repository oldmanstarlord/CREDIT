# Data Dictionary & Feature Specifications

## Application Fields by Category

### Step 1: Universal Personal Details

| Field | Type | Validation | Notes |
|-------|------|-----------|-------|
| full_name | string | 2-255 chars | User's legal name |
| date_of_birth | datetime | Must be 18+ | Used for age only, not scoring |
| gender | string (optional) | M/F/Other | For fairness monitoring only, NOT in model |
| phone_number | string | +91 format | Validated for Indian mobile (6-9 start) |
| email | string | RFC-compliant | Must be unique |
| aadhaar_number | string (optional) | 12 digits | Formatted as XXXX-XXXX-XXXX (masked display) |

### Step 2: Category Selection

One of:
- `farmer` - Agricultural/farming work
- `daily_wage_worker` - Daily labor, construction, domestic work
- `gig_worker` - Platform-based (Ola, Zomato, Uber, etc.)
- `msme_owner` - Small business owner
- `homemaker` - Domestic work, family-dependent
- `low_income_salaried` - Formal employment, <₹80k/month

### Step 3: Category-Specific Data

#### Farmers

| Field | Type | Example | Derived Features |
|-------|------|---------|------------------|
| land_size | float | 2.5 | land_value_proxy = acres × region_price |
| land_location_state | string | Maharashtra | Used for regional pricing |
| land_location_district | string | Nashik | Used for regional pricing |
| land_location_village | string | Pimpalkhed | Locality context |
| crop_type | string | sugarcane | harvest_income_multiplier (map lookup) |
| irrigation_type | string | borewell | irrigation_quality_score: {rainfed:0.5, canal:0.7, borewell:0.85} |
| expected_harvest_months | array[int] | [11,12,1] | Seasonal income flag |
| annual_income_estimate | integer | 150000 | monthly = annual/12 |
| dependent_family_members | integer | 4 | income_per_dependent |
| kisan_credit_card_number | string (optional) | XXXX... | has_kcc: binary signal |

**Computed Features:**
- `land_value_proxy`: Estimated collateral value
- `seasonal_income_flag`: = 1.0 (always seasonal)
- `harvest_income_multiplier`: 2.5-4.0x based on crop type
- `irrigation_quality_score`: 0.5-0.85

#### Daily Wage Workers

| Field | Type | Example | Derived Features |
|-------|------|---------|------------------|
| occupation_type | string | construction_labor | Used for income validation |
| average_daily_earnings | integer | 400 | monthly = daily × days/month |
| days_worked_per_month | integer | 20 | income_stability = days/30 |
| work_consistency | string | irregular | consistency_score: {regular:0.9, irregular:0.5, seasonal:0.4} |
| primary_employer | string (optional) | ABC Constructions | Trust signal |
| has_bank_account | boolean | true | account_status signal |
| upi_transaction_history_consent | boolean | true | Enables UPI data integration |

**Computed Features:**
- `estimated_monthly_income`: daily × days/month
- `income_stability_score`: days_per_month / 30 (0-1)
- `work_consistency_score`: lookup table (0-0.9)

#### Gig Workers

| Field | Type | Example | Derived Features |
|-------|------|---------|------------------|
| platforms | array[string] | ["Ola", "Uber"] | platform_trust_score: max trust score |
| platform_registration_ids | dict | {"Ola": "ID123"} | For verification |
| average_weekly_earnings | integer | 5000 | monthly = weekly × 4.33 |
| active_days_per_week | float | 5.5 | active_day_ratio: days/7 |
| months_on_platform | integer | 18 | platform_tenure_score: min(months/24, 1.0) |
| platform_count | integer | 2 | diversification signal |
| weekly_incomes_history | array[integer] (optional) | [4800, 5200, ...] | weekly_income_cv: std/mean |

**Platform Trust Scores (lookup):**
```
ola: 0.9, uber: 0.9, zomato: 0.85, swiggy: 0.85,
urban_company: 0.8, dunzo: 0.75, rapido: 0.7,
unknown: 0.3
```

**Computed Features:**
- `platform_trust_score`: max of platform scores (0-1)
- `weekly_income_cv`: coefficient of variation (0-5, capped)
- `platform_tenure_score`: months on platform normalized (0-1)
- `active_day_ratio`: active days / 7 (0-1)
- `num_platforms`: count of active platforms

#### MSME Owners

| Field | Type | Example | Derived Features |
|-------|------|---------|------------------|
| business_type | string | retail_shop | Category for rules |
| business_age_months | integer | 18 | business_age_score: min(months/36, 1.0) |
| monthly_revenue | integer | 80000 | profit_margin, cash flow analysis |
| monthly_expenses | integer | 60000 | expense_to_revenue_ratio |
| number_of_employees | integer | 3 | Business scale signal |
| gst_registration_number | string (optional) | 27AABCU9603H1Z0 | has_gst: binary (formalization) |
| udyam_registration_number | string (optional) | UDY123456 | has_udyam: binary (formalization) |
| primary_sales_channel | string | offline | offline/online/both |
| monthly_revenues_history | array[integer] (optional) | [75k, 80k, 85k] | revenue_growth_trend |

**Computed Features:**
- `profit_margin`: (revenue - expenses) / revenue (0-1)
- `expense_to_revenue_ratio`: expenses / revenue (0-1)
- `revenue_growth_trend`: linear trend slope / mean (-1 to 2)
- `cash_flow_volatility`: cv of monthly revenues (0-5, capped)
- `is_formalized`: has_gst OR has_udyam (binary)
- `business_age_score`: tenure normalized (0-1)

#### Homemakers

| Field | Type | Example | Derived Features |
|-------|------|---------|------------------|
| household_monthly_income | integer | 50000 | Primary income source |
| spouse_employment_status | string (optional) | salaried | Context for nominee |
| number_of_dependents | integer | 2 | income_per_dependent |
| household_monthly_expenses | integer | 45000 | Savings buffer calculation |

**Key Requirement:**
- **MUST provide nominee** (spouse, parent, or authorized guarantor)
- Cannot apply without nominee endorsement
- Nominee income and collateral are primary scoring factors

**Computed Features:**
- `household_income`: passthrough (float)
- `income_per_dependent`: household / (dependents + 1)
- `savings_buffer_ratio`: (income - expenses) / expenses

#### Low-Income Salaried

| Field | Type | Example | Derived Features |
|-------|------|---------|------------------|
| employer_name | string | ABC Corp | Context |
| employer_type | string | private | type_score: {govt:0.95, private:0.75, ngo:0.70, informal:0.40} |
| monthly_salary_net | integer | 35000 | Primary income |
| employment_tenure_months | integer | 24 | tenure_score: min(months/36, 1.0) |
| salary_credited_to_bank | boolean | true | Formalization signal |
| bank_name | string (optional) | ICICI | Account context |
| bank_account_number | string (optional) | Masked | Verification |
| salary_slip_uploaded | boolean (optional) | true | Document proof |

**Computed Features:**
- `monthly_salary`: passthrough (float)
- `employment_tenure_score`: normalized (0-1)
- `employment_formalization_score`: employer type lookup (0-0.95)
- `salary_to_account`: salary_credited_to_bank (binary)

### Nominee/Endorsement Data

Applicable to all categories, mandatory for homemakers.

| Field | Type | Validation | Notes |
|-------|------|-----------|-------|
| full_name | string | 2-255 chars | Endorser's legal name |
| relationship | string | valid_list | spouse, parent, sibling, employer, community_leader |
| phone_number | string | Indian format | Must be reachable |
| aadhaar_number | string (optional) | 12 digits | Verification |
| age | integer | ≥ 21 | Minimum age requirement |
| employment_type | string (optional) | Various | Source of endorser income |
| monthly_income | integer | > 0 | income_ratio: nominee / applicant |
| collateral_type | string (optional) | property, vehicle, gold, fd, livestock | Tangible security |
| collateral_value | integer (optional) | > 0 | Stated value before discount |
| collateral_verified | boolean | | Bank verification flag |

**Collateral Discount Factors** (adjusted value = stated × discount):
- property: 0.70 (conservative real estate valuation)
- vehicle: 0.50 (depreciation risk)
- gold: 0.85 (liquid, stable)
- fixed_deposit: 0.90 (highly liquid)
- livestock: 0.40 (mortality risk)

**Computed Features:**
- `nominee_income_ratio`: nominee_income / applicant_income
- `nominee_relationship_score`: lookup table (0.3-0.9)
- `has_verified_collateral`: Boolean
- `collateral_adjusted_value`: stated × discount

---

## Credit Score Calculation

### Score Range: 300-850

**Formula:**
```
base_score = 850 - (probability_of_default × 550)
credit_score = clamp(base_score, 300, 850)
```

**Example:**
- PD = 0.15 → score = 850 - (0.15 × 550) = 767 (Low Risk)
- PD = 0.40 → score = 850 - (0.40 × 550) = 630 (High Risk)
- PD = 0.70 → score = 850 - (0.70 × 550) = 365 (Very High Risk)

### Risk Bands

| Band | Score Range | Label | Action |
|------|-------------|-------|--------|
| Low | 750-850 | Low Risk | Auto-approve eligible applicants |
| Medium | 650-749 | Medium Risk | Hold for analyst review |
| High | 550-649 | High Risk | Senior review required |
| Very High | 300-549 | Very High Risk | Likely rejection |

### Score Breakdown Weights (Dashboard)

| Component | Weight | Points | Rationale |
|-----------|--------|--------|-----------|
| Income Stability | 25% | 0-25 | Ability to maintain income |
| Repayment Capacity | 30% | 0-30 | EMI affordability |
| Spending Data | 15% | 0-15 | Observable spending discipline |
| Profile Completeness | 10% | 0-10 | Data sufficiency |
| Alternative Data | 20% | 0-20 | Platform/transaction history |

**Total = 100 points → scaled to 300-850 range**

---

## ML Model Features (50+ input features)

### Income Standard Ratios

- `monthly_income`: Estimated monthly income (float)
- `loan_to_income_ratio`: requested_amount / (monthly_income × 12)
- `emi_to_income_ratio`: estimated_emi / monthly_income
- `income_stability`: 1 - (income_std / income_mean) [0-1]

### Alternative Behavioral Features

- `transaction_consistency`: UPI/bank transaction regularity [0-1]
- `utility_payment_score`: Bill payment percentages (electricity, phone, rent)
- `savings_buffer_ratio`: avg_savings / monthly_expenses [0-10, capped]
- `spending_pattern_ratio`: essential_spend / total_spend [0-1]
- `cash_flow_volatility`: std(incomes) / mean(incomes) [0-10, capped]
- `has_verified_documents`: Binary flag

### Trust Framework Features

- `has_nominee`: Binary
- `nominee_income_ratio`: nominee_income / applicant_income [0+]
- `has_verified_collateral`: Binary
- `collateral_value`: Adjusted collateral value (₹)
- `nominee_relationship_score`: Quality of relationship [0-1]

### Category-Specific Features

**Farmer:**
- land_size, land_value_proxy, seasonal_income_flag
- harvest_income_multiplier, irrigation_quality_score, has_kcc

**Daily Worker:**
- estimated_monthly_income, income_stability_score, work_consistency_score

**Gig Worker:**
- platform_trust_score, num_platforms, weekly_income_cv
- platform_tenure_score, active_day_ratio

**MSME:**
- monthly_revenue, profit_margin, expense_to_revenue_ratio
- revenue_growth_trend, cash_flow_volatility
- is_formalized, business_age_score

**Homemaker:**
- household_income, income_per_dependent

**Salaried:**
- monthly_salary, employment_tenure_score
- employment_formalization_score, salary_to_account

---

## Output Schemas

### Credit Score Response

```json
{
  "credit_score": 742,
  "score_band": "medium",
  "probability_of_default": 0.183,
  "risk_tier": "Trust Building",
  "eligibility": "APPROVED",
  "suggested_amount": 150000,
  "suggested_tenure_months": 18,
  "interest_rate_min": 16.0,
  "interest_rate_max": 19.0,
  "estimated_emi_min": 9800,
  "estimated_emi_max": 10400,
  "income_stability_score": 22,
  "repayment_capacity_score": 26,
  "spending_data_score": 10,
  "profile_completeness_score": 8,
  "alternative_data_score": 16,
  "top_positive_factors": [
    "Platform tenure strong (18 months)",
    "Consistent weekly earnings pattern"
  ],
  "top_negative_factors": [
    "High income variability (gig nature)",
    "No prior loan history"
  ]
}
```

---

## Validation Rules

### Pre-Screening Thresholds

| Check | Min Value | Status |
|-------|-----------|--------|
| Age | 18 years | Mandatory |
| Income | Category-specific (see config) | Mandatory |
| Document proof | At least 1 | Mandatory |

### Policy Engine Hard Rules

| Rule | Condition | Action |
|------|-----------|--------|
| EMI Affordability | EMI > 30-40% income | REJECT |
| Credit Score | Score < 500 | REJECT |
| PD Threshold | PD > 65% | AUTO-REJECT |
| Exposure Cap | Total > ₹10L | REJECT |
| New User Cap | First loan > ₹50K | REJECT |

---

## Data Integrity Notes

**Protected Attributes (Fairness):**
Never pass to ML model, but collect for post-hoc fairness monitoring:
- Gender
- Religion/caste (if collected)
- Ethnicity/nationality
- Regional/state-level location (use only for land valuation)

**Sensitive PII:**
- Always mask Aadhaar display: XXXX-XXXX-XXXX
- Encrypt bank account numbers
- Hash passwords (bcrypt)
- Log user actions but never log passwords or full account numbers

**Data Retention:**
- Keep application data for 7 years (regulatory requirement)
- Keep audit logs indefinitely (immutable)
- Delete user account data on request (after 1 year of no activity)

---

**Last Updated:** March 2024
