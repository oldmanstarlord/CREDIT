"""
Model prediction and inference
Loads trained model and generates credit decisions with SHAP explanations
"""

import logging
import pickle
from typing import Dict, Tuple, Any
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import xgboost as xgb

from app.ml.feature_engineering import FeatureEngineer
from app.core.config import settings, PLATFORM_TRUST_SCORES
from app.services.trust_service import TrustService

logger = logging.getLogger(__name__)


PILLAR_FEATURE_MAP = {
    'income_stability': [
        'AMT_INCOME_TOTAL',
        'feat_daily_income_stability_proxy',
        'feat_salaried_regularity_proxy',
        'feat_farmer_seasonal_income_flag',
        'feat_gig_income_variability_proxy',
        'feat_daily_monthly_income_proxy',
        'monthly_income',
    ],
    'repayment_capacity': [
        'AMT_CREDIT',
        'AMT_ANNUITY',
        'annuity_to_income_ratio',
        'credit_to_income_ratio',
        'feat_daily_emi_pressure',
        'feat_segment_emi_cap',
        'debt_to_income_ratio',
    ],
    'spending_data': [
        'feat_msme_profitability_proxy',
        'feat_msme_cashflow_proxy',
        'feat_gig_activity_proxy',
    ],
    'profile_completeness': [
        'total_documents_provided',
        'feat_salaried_bankability_proxy',
        'CNT_FAM_MEMBERS',
    ],
    'alternative_data': [
        'feat_gig_platform_trust_proxy',
        'feat_farmer_land_value_proxy',
        'feat_nominee_recommended_all',
        'feat_homemaker_nominee_need',
    ],
}

PILLAR_MAX_SCORES = {
    'income_stability': 25,
    'repayment_capacity': 30,
    'spending_data': 15,
    'profile_completeness': 10,
    'alternative_data': 20,
}


class CreditScorer:
    """
    Production inference engine for credit scoring.
    Loads trained model, scores applications, and generates explanations.
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.model_feature_names = None
        self.model_feature_defaults = {}
        self.calibrator = None
        self.shap_explainer = None
        self.feature_engineer = FeatureEngineer()
        self.trust_service = TrustService()
        self.winner_artifacts = self._load_winner_artifacts()
        
        if model_path:
            self.load_model(model_path)

    def _load_winner_artifacts(self) -> Dict:
        """Load winner lock and denoise artifacts exported by the notebook."""
        project_root = Path(__file__).resolve().parents[3]
        contracts_root = project_root / "ml_pipeline" / "models" / "integration_contracts"

        lock_path = contracts_root / "final_candidate_lock" / "final_candidate_lock.json"
        denoise_path = contracts_root / "advanced_controls" / "frozen_denoise_params.json"

        artifacts = {
            "segment_thresholds": {},
            "core_segment_pass": False,
            "all_segment_pass": False,
            "winner_name": settings.ML_MODEL_VERSION,
            "winsor_params": {},
            "log_columns": [],
            "uncertainty_band": (0.45, 0.55),
            "ood_rate_threshold": 0.10,
            "missing_critical_threshold": 0.40,
        }

        try:
            if lock_path.exists():
                payload = json.loads(lock_path.read_text(encoding="utf-8"))
                lock = payload.get("lock", {})
                artifacts["segment_thresholds"] = lock.get("segment_thresholds", {})
                artifacts["core_segment_pass"] = bool(lock.get("core_segment_recall_pass", False))
                artifacts["all_segment_pass"] = bool(lock.get("all_segment_recall_pass", False))
                artifacts["winner_name"] = lock.get("final_candidate", artifacts["winner_name"])
            if denoise_path.exists():
                denoise = json.loads(denoise_path.read_text(encoding="utf-8"))
                artifacts["winsor_params"] = denoise.get("winsor_params", {})
                artifacts["log_columns"] = denoise.get("log_columns", [])
        except Exception as e:
            logger.warning("Could not load notebook integration artifacts: %s", e)

        return artifacts

    def get_go_live_status(self) -> Dict:
        """Expose go-live gate status based on notebook lock artifacts."""
        return {
            "winner_name": self.winner_artifacts.get("winner_name"),
            "core_segment_recall_pass": self.winner_artifacts.get("core_segment_pass", False),
            "all_segment_recall_pass": self.winner_artifacts.get("all_segment_pass", False),
            "publish_allowed": bool(self.winner_artifacts.get("core_segment_pass", False)),
        }
    
    def load_model(self, model_path: str):
        """
        Load trained XGBoost model.
        
        Args:
            model_path: Path to saved model
        """
        try:
            path = Path(model_path)
            if path.suffix.lower() in {'.pkl', '.pickle'}:
                with open(path, 'rb') as f:
                    payload = pickle.load(f)
                if isinstance(payload, dict):
                    self.model = payload.get('best_model') or payload.get('model') or payload.get('estimator')
                    self.model_feature_names = payload.get('feature_names') or payload.get('train_features')
                    self.model_feature_defaults = payload.get('feature_defaults', {}) or {}
                    self.calibrator = payload.get('calibrator')
                    # Winner notebook artifact can carry serving controls; prefer them when present.
                    if payload.get('segment_thresholds'):
                        self.winner_artifacts['segment_thresholds'] = payload.get('segment_thresholds', {})
                    if payload.get('winner_name'):
                        self.winner_artifacts['winner_name'] = payload.get('winner_name')
                    if payload.get('uncertainty_band'):
                        ub = payload.get('uncertainty_band')
                        self.winner_artifacts['uncertainty_band'] = (float(ub[0]), float(ub[1]))
                    if payload.get('ood_rate_threshold') is not None:
                        self.winner_artifacts['ood_rate_threshold'] = float(payload.get('ood_rate_threshold'))
                    if payload.get('missing_critical_threshold') is not None:
                        self.winner_artifacts['missing_critical_threshold'] = float(payload.get('missing_critical_threshold'))
                    if payload.get('winsor_params'):
                        self.winner_artifacts['winsor_params'] = payload.get('winsor_params', {})
                    if payload.get('log_columns'):
                        self.winner_artifacts['log_columns'] = payload.get('log_columns', [])
                    final_lock = payload.get('final_lock', {}).get('lock', {}) if isinstance(payload.get('final_lock', {}), dict) else {}
                    if final_lock:
                        self.winner_artifacts['core_segment_pass'] = bool(final_lock.get('core_segment_recall_pass', self.winner_artifacts.get('core_segment_pass', False)))
                        self.winner_artifacts['all_segment_pass'] = bool(final_lock.get('all_segment_recall_pass', self.winner_artifacts.get('all_segment_pass', False)))
                    if self.model is None:
                        raise ValueError("Pickle payload does not contain a supported model key")
                else:
                    self.model = payload
            else:
                self.model = xgb.XGBClassifier()
                self.model.load_model(model_path)
                self.model_feature_names = None
                self.calibrator = None
            logger.info(f"Model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _get_feature_names(self):
        if hasattr(self.model, "get_booster"):
            booster_names = self.model.get_booster().feature_names
            if booster_names:
                return booster_names
        if self.model_feature_names:
            return list(self.model_feature_names)
        if hasattr(self.model, "feature_names_in_"):
            return list(getattr(self.model, "feature_names_in_"))
        return []
    
    def load_shap_explainer(self, explainer_path: str):
        """
        Load SHAP explainer.
        
        Args:
            explainer_path: Path to saved SHAP explainer
        """
        try:
            with open(explainer_path, 'rb') as f:
                self.shap_explainer = pickle.load(f)
            logger.info(f"SHAP explainer loaded from {explainer_path}")
        except Exception as e:
            logger.error(f"Failed to load SHAP explainer: {e}")
    
    def score_application(self, application_data: Dict) -> Dict:
        """
        Score a loan application end-to-end.
        
        Process:
        1. Engineer features from raw application data
        2. Run XGBoost model to get Probability of Default
        3. Convert PD to 300-850 credit score
        4. Classify into risk band
        5. Recommend loan terms
        6. Generate SHAP explanation
        
        Args:
            application_data: Raw application dictionary
        
        Returns:
            Dictionary with score, PD, recommendation, and explanation
        """
        
        if not self.model:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Feature engineering (or direct notebook-feature payload pass-through).
        feature_names = self._get_feature_names()
        if feature_names:
            raw_overlap = sum(1 for feat in feature_names if feat in application_data)
            raw_overlap_ratio = raw_overlap / max(len(feature_names), 1)
        else:
            raw_overlap_ratio = 0.0
        direct_feature_payload = bool(feature_names and raw_overlap_ratio >= 0.90)

        if direct_feature_payload:
            features_dict = {feat: float(application_data.get(feat, 0.0) or 0.0) for feat in feature_names}
        else:
            # Deterministic adapter for raw application payload -> notebook winner contract.
            if feature_names and any(col in feature_names for col in ['AMT_INCOME_TOTAL', 'AMT_CREDIT', 'EXT_SOURCE_1']):
                features_dict = self._build_winner_contract_features(application_data, feature_names)
            else:
                features_dict = self.feature_engineer.engineer_all_features(application_data)

        if not feature_names:
            feature_names = sorted(features_dict.keys())

        feature_overlap = sum(1 for feat in feature_names if feat in features_dict)
        overlap_ratio = feature_overlap / max(len(feature_names), 1)
        if overlap_ratio < 0.60:
            raise ValueError(
                "Feature contract mismatch: model expects notebook features that are not present in backend runtime. "
                "Export and wire the winner model + feature contract from notebook artifacts before scoring."
            )
        features_list = [features_dict.get(feat, 0.0) for feat in feature_names]

        # Freeze denoise transform from notebook artifacts.
        features_list = self._apply_frozen_denoise(
            feature_names=feature_names,
            feature_values=features_list,
        )
        X = pd.DataFrame([features_list], columns=feature_names)
        
        # Get probability of default from the base model.
        # Calibrator is optional and explicitly opt-in because serialized
        # calibration objects are version-sensitive across sklearn releases.
        base_pd_proba = float(self.model.predict_proba(X)[0, 1])
        pd_proba = base_pd_proba
        if self.calibrator is not None and settings.ML_USE_CALIBRATOR:
            try:
                calibrated = float(self.calibrator.predict_proba(X)[0, 1])
                if np.isfinite(calibrated):
                    pd_proba = calibrated
            except Exception as e:
                logger.warning("Calibrator failed, falling back to base model probability: %s", e)

        # Base score before trust adjustment (used for initial affordability estimate).
        base_credit_score = self._pd_to_credit_score(pd_proba)
        
        # Recommend loan terms
        loan_recommendation = self._recommend_loan_terms(
            base_credit_score, pd_proba, features_dict, application_data
        )

        # Trust-backed nominee adjustment is available to all categories.
        adjusted_pd, trust_details = self._apply_nominee_trust_adjustment(
            base_pd=pd_proba,
            loan_recommendation=loan_recommendation,
            application_data=application_data,
        )

        # Final score/risk uses nominee-adjusted PD when nominee data exists.
        credit_score = self._pd_to_credit_score(adjusted_pd)
        risk_band = self._classify_risk_band(credit_score)

        # Winner lock policy thresholding + guardrails.
        segment_name = self._resolve_segment_name(application_data)
        threshold = self._resolve_segment_threshold(segment_name)
        decision_with_guardrails = self._guardrail_decision(
            adjusted_pd=adjusted_pd,
            threshold=threshold,
            features_dict=features_dict,
            application_data=application_data,
            feature_names=feature_names,
            direct_feature_payload=direct_feature_payload,
        )

        # Refresh recommendation based on final adjusted risk profile.
        loan_recommendation = self._recommend_loan_terms(
            credit_score, adjusted_pd, features_dict, application_data
        )
        
        # Generate SHAP explanation (lazy-create TreeExplainer if not preloaded).
        if self.shap_explainer is None and self.model is not None:
            try:
                import shap
                self.shap_explainer = shap.TreeExplainer(self.model)
            except Exception as e:
                logger.warning(f"Could not create SHAP explainer: {e}")

        shap_explanation = self._explain_prediction(
            X, features_dict, application_data
        ) if self.shap_explainer else None

        pillar_scores = self._compute_pillar_scores(
            shap_explanation=shap_explanation,
            probability_of_default=adjusted_pd,
        )
        
        return {
            'probability_of_default': adjusted_pd,
            'base_probability_of_default': base_pd_proba,
            'credit_score': credit_score,
            'risk_band': risk_band,
            'segment_name': segment_name,
            'segment_threshold': threshold,
            'decision_status': decision_with_guardrails['decision_status'],
            'reason_flag': decision_with_guardrails['reason_flag'],
            'confidence_tier': decision_with_guardrails['confidence_tier'],
            'predicted_default_flag': decision_with_guardrails['predicted_default_flag'],
            'missing_critical_rate': decision_with_guardrails['missing_critical_rate'],
            'ood_rate': decision_with_guardrails['ood_rate'],
            'loan_recommendation': loan_recommendation,
            'shap_explanation': shap_explanation,
            'pillar_scores': pillar_scores,
            'trust_adjustment': trust_details,
            'model_version': self.winner_artifacts.get('winner_name', settings.ML_MODEL_VERSION),
            'features_computed': features_dict
        }

    def _compute_pillar_scores(self, shap_explanation: Dict[str, Any], probability_of_default: float) -> Dict[str, int]:
        """
        Convert feature-level SHAP contributions into normalized 5-pillar scores.
        Falls back to a PD heuristic if SHAP is unavailable.
        """
        if not shap_explanation or not isinstance(shap_explanation, dict):
            pd_safe = min(max(float(probability_of_default or 0.5), 0.0), 1.0)
            base_strength = max(0.0, 1.0 - pd_safe)
            return {
                'income_stability': int(round(PILLAR_MAX_SCORES['income_stability'] * base_strength * 0.95)),
                'repayment_capacity': int(round(PILLAR_MAX_SCORES['repayment_capacity'] * base_strength)),
                'spending_data': int(round(PILLAR_MAX_SCORES['spending_data'] * max(0.0, base_strength - 0.05))),
                'profile_completeness': int(round(PILLAR_MAX_SCORES['profile_completeness'] * max(0.0, base_strength - 0.10))),
                'alternative_data': int(round(PILLAR_MAX_SCORES['alternative_data'] * max(0.0, base_strength - 0.08))),
            }

        shap_values = shap_explanation.get('shap_values', {}) or {}
        abs_map = {k: abs(float(v)) for k, v in shap_values.items()}

        raw_totals = {}
        for pillar, features in PILLAR_FEATURE_MAP.items():
            raw_totals[pillar] = sum(abs_map.get(f, 0.0) for f in features)

        total_signal = sum(raw_totals.values())
        if total_signal <= 0:
            # If SHAP exists but map overlap is empty, use flat neutral defaults.
            return {
                'income_stability': 12,
                'repayment_capacity': 15,
                'spending_data': 8,
                'profile_completeness': 5,
                'alternative_data': 10,
            }

        scores = {}
        for pillar, max_score in PILLAR_MAX_SCORES.items():
            normalized = raw_totals.get(pillar, 0.0) / total_signal
            # Spread around mid-range so low-signal pillars are not always near zero.
            blended = (0.35 + 0.65 * normalized)
            scores[pillar] = int(round(min(max_score, max(0.0, blended * max_score))))

        return scores

    def _build_winner_contract_features(self, application_data: Dict, feature_names) -> Dict:
        defaults = {k: float(v) for k, v in (self.model_feature_defaults or {}).items() if isinstance(v, (int, float))}
        out = {k: float(defaults.get(k, 0.0)) for k in feature_names}

        weekly_income = float(application_data.get('average_weekly_earnings') or 0.0)
        monthly_income = float(
            application_data.get('monthly_income')
            or application_data.get('avg_monthly_income')
            or application_data.get('monthly_salary_net')
            or application_data.get('household_monthly_income')
            or (weekly_income * 4.33 if weekly_income > 0 else 0.0)
            or 0.0
        )
        annual_income = float(
            application_data.get('annual_income_estimate')
            or (monthly_income * 12.0 if monthly_income > 0 else out.get('AMT_INCOME_TOTAL', 0.0))
        )
        requested_amount = float(application_data.get('requested_amount') or out.get('AMT_CREDIT', 0.0))
        tenure = int(application_data.get('requested_tenure_months') or 12)
        household_size = float(application_data.get('household_size') or out.get('CNT_FAM_MEMBERS', 1.0) or 1.0)

        age = application_data.get('age')
        if age is None and application_data.get('date_of_birth'):
            try:
                dob = datetime.fromisoformat(str(application_data.get('date_of_birth')).replace('Z', '+00:00'))
                age = max(18, int((datetime.utcnow() - dob.replace(tzinfo=None)).days / 365.25))
            except Exception:
                age = None
        age = float(age if age is not None else max(18.0, abs(out.get('DAYS_BIRTH', -35 * 365)) / 365.0))

        annuity_ratio = float(application_data.get('annuity_to_income_ratio') or 0.0)
        credit_ratio = float(application_data.get('credit_to_income_ratio') or 0.0)

        if annuity_ratio <= 0 and annual_income > 0:
            approx_monthly_emi = float(self._estimate_emi(requested_amount, tenure, 18.0)) if requested_amount > 0 else 0.0
            annuity_ratio = approx_monthly_emi / max((annual_income / 12.0), 1.0)
        if credit_ratio <= 0 and annual_income > 0:
            credit_ratio = requested_amount / max(annual_income, 1.0)

        out['AMT_INCOME_TOTAL'] = annual_income
        out['AMT_CREDIT'] = requested_amount
        out['AMT_GOODS_PRICE'] = requested_amount if requested_amount > 0 else out.get('AMT_GOODS_PRICE', 0.0)
        out['AMT_ANNUITY'] = (annuity_ratio * max(annual_income / 12.0, 0.0))
        out['CNT_FAM_MEMBERS'] = max(1.0, household_size)
        out['CNT_CHILDREN'] = max(0.0, household_size - 2.0)
        out['DAYS_BIRTH'] = -abs(age * 365.0)

        if 'credit_to_income_ratio' in out:
            out['credit_to_income_ratio'] = credit_ratio
        if 'annuity_to_income_ratio' in out:
            out['annuity_to_income_ratio'] = annuity_ratio
        if 'credit_to_goods_ratio' in out and out.get('AMT_GOODS_PRICE', 0.0) > 0:
            out['credit_to_goods_ratio'] = out['AMT_CREDIT'] / max(out['AMT_GOODS_PRICE'], 1.0)
        if 'income_per_family_member' in out:
            out['income_per_family_member'] = annual_income / max(out['CNT_FAM_MEMBERS'], 1.0)
        if 'employment_to_age_ratio' in out:
            days_emp = abs(float(out.get('DAYS_EMPLOYED', -2000.0)))
            out['employment_to_age_ratio'] = min(1.0, (days_emp / 365.0) / max(age, 1.0))

        docs = [
            bool(application_data.get('has_bank_account')),
            bool(application_data.get('bank_statement_uploaded')),
            bool(application_data.get('employer_letter_uploaded')),
            bool(application_data.get('land_document_uploaded')),
            bool(application_data.get('docs_verified')),
        ]
        if 'total_documents_provided' in out:
            out['total_documents_provided'] = float(sum(docs))

        inq_month = float(application_data.get('recent_inquiries_1m') or 0.0)
        inq_year = float(application_data.get('recent_inquiries_12m') or (inq_month * 4.0))
        if 'enquiry_last_month' in out:
            out['enquiry_last_month'] = inq_month
        if 'enquiry_last_year' in out:
            out['enquiry_last_year'] = inq_year
        if 'enquiry_acceleration' in out:
            out['enquiry_acceleration'] = inq_month / max((inq_year / 12.0), 1e-6)

        seg = str(application_data.get('user_category') or 'low_income_salaried').strip().lower()
        emi_caps = {
            'farmer': 0.30,
            'daily_wage_worker': 0.25,
            'gig_worker': 0.35,
            'msme_owner': 0.40,
            'homemaker': 0.22,
            'low_income_salaried': 0.40,
        }

        out['feat_farmer_land_value_proxy'] = float(application_data.get('land_size', 0.0)) * float(application_data.get('region_land_price_per_acre', 200000.0))
        out['feat_farmer_harvest_buffer'] = float(application_data.get('harvest_buffer_months', 2.0))
        out['feat_farmer_seasonal_income_flag'] = 1.0 if seg == 'farmer' else 0.0

        out['feat_daily_income_stability_proxy'] = float(application_data.get('work_consistency_score', 0.5))
        out['feat_daily_monthly_income_proxy'] = float(application_data.get('average_daily_earnings', 0.0)) * float(application_data.get('days_worked_per_month', 22.0))
        out['feat_daily_emi_pressure'] = annuity_ratio

        platforms = application_data.get('platforms') or []
        platform_count = float(application_data.get('platform_count') or len(platforms) or 0.0)
        derived_platform_trust = 0.3
        if isinstance(platforms, list) and platforms:
            scores = [PLATFORM_TRUST_SCORES.get(str(p).lower(), 0.3) for p in platforms]
            derived_platform_trust = max(scores) if scores else 0.3
        elif platform_count > 0:
            derived_platform_trust = min(0.85, 0.4 + (0.12 * platform_count))

        active_days = float(application_data.get('active_days_per_week') or 0.0)
        derived_income_variability = max(0.0, min(1.0, 1.0 - (active_days / 7.0))) if active_days > 0 else 0.5

        out['feat_gig_platform_trust_proxy'] = float(
            application_data.get('platform_trust_score')
            or application_data.get('digital_payment_ratio')
            or derived_platform_trust
        )
        out['feat_gig_income_variability_proxy'] = float(
            application_data.get('weekly_income_cv')
            or application_data.get('income_variability')
            or derived_income_variability
        )
        out['feat_gig_activity_proxy'] = float(application_data.get('active_days_per_week', 4.0)) / 7.0

        revenue = float(application_data.get('monthly_revenue', 0.0))
        expenses = float(application_data.get('monthly_expenses', 0.0))
        out['feat_msme_profitability_proxy'] = ((revenue - expenses) / max(revenue, 1.0)) if revenue > 0 else 0.0
        out['feat_msme_growth_proxy'] = float(application_data.get('revenue_growth_trend', 0.0))
        out['feat_msme_cashflow_proxy'] = float(application_data.get('cash_flow_volatility', 0.5))

        out['feat_homemaker_household_income_proxy'] = annual_income
        out['feat_homemaker_dependency_ratio'] = max(0.0, household_size - 1.0) / max(household_size, 1.0)
        out['feat_homemaker_nominee_need'] = 1.0 if seg == 'homemaker' else 0.0

        out['feat_salaried_regularity_proxy'] = float(application_data.get('salary_regularity_score', 0.7))
        out['feat_salaried_bankability_proxy'] = 1.0 if bool(application_data.get('has_bank_account')) else 0.0

        out['feat_nominee_recommended_all'] = 1.0 if bool(application_data.get('nominee')) else 0.0
        out['feat_segment_emi_cap'] = float(emi_caps.get(seg, 0.35))

        return {k: float(out.get(k, 0.0) or 0.0) for k in feature_names}

    def _resolve_segment_name(self, application_data: Dict) -> str:
        seg = str(application_data.get('user_category', 'low_income_salaried')).strip().lower()
        valid = set(self.winner_artifacts.get('segment_thresholds', {}).keys())
        if seg in valid:
            return seg
        if 'low_income_salaried' in valid:
            return 'low_income_salaried'
        return next(iter(valid), 'default')

    def _resolve_segment_threshold(self, segment_name: str) -> float:
        seg_thr = self.winner_artifacts.get('segment_thresholds', {})
        if segment_name in seg_thr:
            return float(seg_thr[segment_name])
        if seg_thr:
            return float(np.mean(list(seg_thr.values())))
        return float(settings.DECISION_THRESHOLD)

    def _apply_frozen_denoise(self, feature_names, feature_values):
        winsor = self.winner_artifacts.get('winsor_params', {})
        log_cols = set(self.winner_artifacts.get('log_columns', []))
        out = []
        for name, val in zip(feature_names, feature_values):
            v = float(val) if val is not None else 0.0
            b = winsor.get(name)
            if b:
                v = min(max(v, float(b.get('q01', v))), float(b.get('q99', v)))
            if name in log_cols:
                v = float(np.log1p(max(v, 0.0)))
            out.append(v)
        return out

    def _guardrail_decision(
        self,
        adjusted_pd: float,
        threshold: float,
        features_dict: Dict,
        application_data: Dict,
        feature_names=None,
        direct_feature_payload: bool = False,
    ) -> Dict:
        if direct_feature_payload:
            contract_critical = [
                'AMT_INCOME_TOTAL',
                'credit_to_income_ratio',
                'annuity_to_income_ratio',
                'CNT_FAM_MEMBERS',
            ]
            existing = [k for k in contract_critical if (feature_names and k in feature_names) or k in features_dict]
            if not existing:
                existing = contract_critical
            missing = sum(1 for k in existing if features_dict.get(k) in (None, 0, 0.0))
            missing_rate = missing / max(len(existing), 1)
        else:
            critical = [
                'monthly_income',
                'debt_to_income_ratio',
                'annuity_to_income_ratio',
                'credit_to_income_ratio',
                'household_size',
            ]
            missing = sum(1 for k in critical if application_data.get(k) is None and features_dict.get(k) in (None, 0, 0.0))
            missing_rate = missing / max(len(critical), 1)

        winsor = self.winner_artifacts.get('winsor_params', {})
        ood_flags = 0
        ood_total = 0
        for k, b in winsor.items():
            if k in features_dict:
                ood_total += 1
                v = float(features_dict.get(k, 0.0) or 0.0)
                if v < float(b.get('q01', v)) or v > float(b.get('q99', v)):
                    ood_flags += 1
        ood_rate = (ood_flags / ood_total) if ood_total else 0.0

        low, high = self.winner_artifacts.get('uncertainty_band', (0.45, 0.55))
        uncertain = low <= adjusted_pd <= high
        ood_hold = ood_rate > float(self.winner_artifacts.get('ood_rate_threshold', 0.10))
        missing_hold = missing_rate > float(self.winner_artifacts.get('missing_critical_threshold', 0.40))

        pred_default = int(adjusted_pd >= threshold)
        manual_review = uncertain or ood_hold or missing_hold

        if missing_hold:
            decision_status = 'insufficient_data'
            reason = 'critical_missingness'
        elif manual_review:
            decision_status = 'manual_review'
            reason = 'out_of_distribution' if ood_hold else 'uncertain_pd_band'
        else:
            decision_status = 'auto_reject_high_risk' if pred_default == 1 else 'auto_approve_low_risk'
            reason = 'normal_scoring'

        delta = abs(adjusted_pd - threshold)
        if manual_review:
            confidence = 'low'
        elif delta >= 0.15 and ood_rate <= 0.05:
            confidence = 'high'
        else:
            confidence = 'medium'

        return {
            'predicted_default_flag': pred_default,
            'decision_status': decision_status,
            'reason_flag': reason,
            'confidence_tier': confidence,
            'missing_critical_rate': float(missing_rate),
            'ood_rate': float(ood_rate),
        }

    def _apply_nominee_trust_adjustment(
        self,
        base_pd: float,
        loan_recommendation: Dict,
        application_data: Dict,
    ) -> Tuple[float, Dict]:
        """Apply nominee trust adjustment for any category when nominee data is present."""
        nominee_data = application_data.get("nominee")
        if not nominee_data:
            return base_pd, {
                "applied": False,
                "reason": "No nominee provided",
                "adjustment": 0.0,
            }

        # Include estimated EMI so trust service can evaluate income coverage.
        enriched_nominee = dict(nominee_data)
        enriched_nominee["estimated_emi"] = loan_recommendation.get("estimated_emi_max", 0)

        eligible, eligibility_reason = self.trust_service.validate_endorser_eligibility(enriched_nominee)
        if not eligible:
            return base_pd, {
                "applied": False,
                "reason": f"Nominee not eligible: {eligibility_reason}",
                "adjustment": 0.0,
            }

        collateral_type = enriched_nominee.get("collateral_type")
        collateral_value = enriched_nominee.get("collateral_value")
        collateral_verified = False
        if collateral_type and collateral_value:
            collateral_verified, _ = self.trust_service.validate_collateral(
                {"type": collateral_type, "value": collateral_value}
            )

        adjusted_pd = self.trust_service.apply_trust_adjustment(
            base_probability_of_default=base_pd,
            nominee_data=enriched_nominee,
            collateral_verified=collateral_verified,
        )

        return adjusted_pd, {
            "applied": True,
            "reason": "Nominee adjustment applied",
            "adjustment": float(adjusted_pd - base_pd),
            "collateral_verified": collateral_verified,
            "nominee_relationship": enriched_nominee.get("relationship"),
        }
    
    def _pd_to_credit_score(self, pd: float) -> int:
        """
        Convert Probability of Default to 300-850 credit score.
        
        Formula: score = 850 - (pd * 550)
        Adjusted by feature strength (0-20 pt bonus for good alternative data)
        
        Args:
            pd: Probability of default (0.0-1.0)
        
        Returns:
            Credit score (300-850)
        """
        base_score = 850 - (pd * 550)
        
        # Cap to valid range
        score = max(300, min(850, int(base_score)))
        
        return score
    
    def _classify_risk_band(self, score: int) -> str:
        """Classify credit score into risk band"""
        if score >= 750:
            return "low"
        elif score >= 650:
            return "medium"
        elif score >= 550:
            return "high"
        else:
            return "very_high"
    
    def _recommend_loan_terms(self, credit_score: int, pd: float, 
                             features_dict: Dict, 
                             application_data: Dict) -> Dict:
        """
        Recommend loan amount, tenure, and interest rate.
        
        Based on:
        - Credit score (tier eligibility)
        - PD (discount/premium for interest)
        - Income (affordability)
        - Category (product mix)
        """
        requested_amount = application_data.get('requested_amount', 50000)
        requested_tenure = application_data.get('requested_tenure_months', 12)
        
        # Determine eligible amount based on credit tier
        eligible_amount = self._calculate_eligible_amount(
            credit_score, features_dict, application_data
        )
        approved_amount = min(requested_amount, eligible_amount)
        
        # Calculate interest rate based on PD and amount tier
        interest_rate_min, interest_rate_max = self._calculate_interest_rate(
            approved_amount, pd, credit_score
        )
        
        # Estimate EMI
        emi_min = self._estimate_emi(approved_amount, requested_tenure, interest_rate_max)
        emi_max = self._estimate_emi(approved_amount, requested_tenure, interest_rate_min)
        
        return {
            'eligible_amount': eligible_amount,
            'recommended_amount': approved_amount,
            'recommended_tenure_months': requested_tenure,
            'interest_rate_min': round(interest_rate_min, 2),
            'interest_rate_max': round(interest_rate_max, 2),
            'estimated_emi_min': int(emi_min),
            'estimated_emi_max': int(emi_max)
        }
    
    def _calculate_eligible_amount(self, score: int, features_dict: Dict, 
                                  app_data: Dict) -> int:
        """Determine max eligible loan amount"""
        
        # Tier-based limits
        if score < 500:
            max_amount = 0  # Not eligible
        elif score < 550:
            max_amount = 25000
        elif score < 650:
            max_amount = 100000
        elif score < 750:
            max_amount = 500000
        else:
            max_amount = 1000000
        
        # Adjust based on income
        monthly_income = features_dict.get('monthly_income', 10000)
        affordability_limit = monthly_income * 12 * 4  # Max 4x annual income
        
        eligible = min(max_amount, int(affordability_limit))
        
        return eligible
    
    def _calculate_interest_rate(self, amount: int, pd: float, 
                                score: int) -> Tuple[float, float]:
        """Calculate interest rate range based on amount and risk"""
        
        # Base rate by amount
        if amount <= 100000:
            base_min, base_max = 18, 25
        elif amount <= 300000:
            base_min, base_max = 12, 18
        elif amount <= 1000000:
            base_min, base_max = 10, 12
        else:
            base_min, base_max = 8, 10
        
        # Risk adjustment based on PD
        risk_spread = (pd - 0.15) * 100  # 0% spread for PD=0.15, 50% spread for PD=0.65
        risk_adj = max(0, min(5, risk_spread))
        
        rate_min = base_min + risk_adj
        rate_max = base_max + risk_adj
        
        return rate_min, rate_max
    
    @staticmethod
    def _estimate_emi(principal: int, tenure_months: int, 
                     annual_rate: float) -> float:
        """Estimate monthly EMI with given rate"""
        if principal <= 0 or tenure_months <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 100 / 12
        if monthly_rate == 0:
            return principal / tenure_months
        
        numerator = principal * monthly_rate * (1 + monthly_rate) ** tenure_months
        denominator = (1 + monthly_rate) ** tenure_months - 1
        
        return numerator / denominator
    
    def _explain_prediction(self, X: np.ndarray, features_dict: Dict,
                           app_data: Dict) -> Dict:
        """Generate SHAP explanation"""
        
        try:
            shap_values = self.shap_explainer.shap_values(X)
            
            # Get feature names from model
            feature_names = self._get_feature_names()
            if not feature_names:
                feature_names = list(features_dict.keys())
            
            # Map SHAP values to feature names
            shap_dict = dict(zip(feature_names, shap_values[0]))
            
            # Get top factors
            indexed = list(zip(feature_names, shap_values[0]))
            
            top_positive = sorted(
                indexed, key=lambda x: x[1], reverse=True
            )[:5]
            
            top_negative = sorted(
                indexed, key=lambda x: x[1]
            )[:5]
            
            expected = self.shap_explainer.expected_value
            if isinstance(expected, (list, tuple, np.ndarray)):
                expected = expected[0]

            return {
                'base_value': float(expected),
                'shap_values': {k: float(v) for k, v in shap_dict.items()},
                'top_positive_factors': [
                    {'feature': name, 'value': float(val)} 
                    for name, val in top_positive
                ],
                'top_negative_factors': [
                    {'feature': name, 'value': float(val)} 
                    for name, val in top_negative
                ]
            }
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return None
