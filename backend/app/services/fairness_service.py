"""
Fairness monitoring service: Detects discriminatory patterns in lending decisions.

Monitors for disparate impact and ensures compliance with Fair Practices Code.
CRITICAL: Protected attributes (gender, region, religion, caste) are NEVER used
in model training. They are collected ONLY for post-hoc fairness monitoring.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FairnessMonitor:
    """
    Monitors for discriminatory patterns in scoring and decisions.
    Runs batch fairness analysis on historical decisions.
    
    Key metric: Disparate Impact Ratio (DIR)
    - DIR = (minority group approval rate) / (majority group approval rate)
    - Threshold: DIR should be >= 0.80 (Four-Fifths Rule)
    - DIR < 0.80 suggests potential discrimination
    """
    
    # Protected attributes that trigger fairness monitoring
    PROTECTED_ATTRIBUTES = ['gender', 'region', 'religion', 'caste', 'age']
    
    # Demographic groups to monitor (intersectionally)
    DEMOGRAPHIC_GROUPS = {
        'gender': ['male', 'female', 'other'],
        'region': ['urban', 'rural', 'semi_urban'],
        'age_group': ['18-25', '26-35', '36-45', '46-55', '56+'],
        'user_category': ['farmer', 'daily_wage_worker', 'gig_worker', 
                         'msme_owner', 'homemaker', 'low_income_salaried']
    }
    
    # Thresholds for bias detection
    DISPARATE_IMPACT_THRESHOLD = 0.80  # Four-Fifths Rule
    PERFORMANCE_DIFFERENTIAL_THRESHOLD = 0.05  # 5pp difference in AUC
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize fairness monitor with database connection"""
        self.db = db
    
    def compute_approval_rate_by_group(self, decisions: List[Dict], 
                                       group_attr: str) -> Dict[str, float]:
        """
        Compute approval rate for each subgroup.
        
        Args:
            decisions: List of application decision records
            group_attr: Attribute to group by (e.g., 'gender', 'region')
        
        Returns:
            Dict mapping group value → approval rate (0-1)
        """
        groups = {}
        
        for decision in decisions:
            group_val = decision.get(group_attr)
            if group_val not in groups:
                groups[group_val] = {'approved': 0, 'total': 0}
            
            groups[group_val]['total'] += 1
            if decision.get('final_decision') == 'approved':
                groups[group_val]['approved'] += 1
        
        approval_rates = {
            group: info['approved'] / info['total'] if info['total'] > 0 else 0
            for group, info in groups.items()
        }
        
        return approval_rates
    
    def compute_disparate_impact_ratio(self, approval_rates: Dict[str, float]) -> Dict:
        """
        Calculate disparate impact ratios (DIR) for all groups.
        
        DIR = (minority group approval rate) / (majority group approval rate)
        A DIR < 0.80 suggests potential discrimination (Four-Fifths Rule).
        
        Args:
            approval_rates: Dict mapping group → approval rate
        
        Returns:
            {
                'ratios': {group_pair: dir_value},
                'flags': [group_pairs with DIR < 0.80],
                'max_disparate_diff': float (largest approval rate difference)
            }
        """
        ratios = {}
        flags = []
        
        groups_sorted = sorted(approval_rates.items(), 
                              key=lambda x: x[1], reverse=True)
        
        for i, (group_a, rate_a) in enumerate(groups_sorted):
            for group_b, rate_b in groups_sorted[i+1:]:
                if rate_a > 0:
                    dir_val = rate_b / rate_a  # minority / majority
                    pair_key = f"{group_b}_vs_{group_a}"
                    ratios[pair_key] = round(dir_val, 3)
                    
                    if dir_val < self.DISPARATE_IMPACT_THRESHOLD:
                        flags.append({
                            'pair': pair_key,
                            'dir': dir_val,
                            'severity': 'HIGH' if dir_val < 0.70 else 'MEDIUM',
                            'group_a_rate': rate_a,
                            'group_b_rate': rate_b,
                            'approval_gap': round(rate_a - rate_b, 3)
                        })
        
        max_diff = max([rate for rate in approval_rates.values()], default=0) - \
                   min([rate for rate in approval_rates.values()], default=0)
        
        return {
            'ratios': ratios,
            'flags': sorted(flags, key=lambda x: x['dir']),
            'max_approval_rate_difference': round(max_diff, 3),
            'bias_detected': len(flags) > 0
        }
    
    def compute_subgroup_performance_metrics(self, predictions: List[Dict], 
                                            actuals: List[int],
                                            subgroup_labels: List[str]) -> Dict:
        """
        Compute ML model performance separately for each demographic subgroup.
        
        Checks for performance disparities (e.g., lower AUC for certain groups).
        
        Args:
            predictions: Model probability outputs (0-1)
            actuals: True labels (0=repaid, 1=defaulted)
            subgroup_labels: Group membership for each sample
        
        Returns:
            {
                'subgroup_performance': {
                    group: {'auc': float, 'precision': float, 'recall': float, 'n_samples': int}
                },
                'performance_disparities': [flagged group pairs]
            }
        """
        from sklearn.metrics import roc_auc_score, precision_score, recall_score
        
        subgroups = {}
        unique_groups = set(subgroup_labels)
        
        for group in unique_groups:
            indices = [i for i, g in enumerate(subgroup_labels) if g == group]
            
            if len(indices) < 2:
                continue  # Skip groups with < 2 samples
            
            group_preds = [predictions[i] for i in indices]
            group_actuals = [actuals[i] for i in indices]
            
            try:
                auc = roc_auc_score(group_actuals, group_preds)
                # Use threshold=0.5 for binary metrics
                binary_preds = [1 if p >= 0.5 else 0 for p in group_preds]
                prec = precision_score(group_actuals, binary_preds, zero_division=0)
                recall = recall_score(group_actuals, binary_preds, zero_division=0)
                
                subgroups[group] = {
                    'auc': round(auc, 3),
                    'precision': round(prec, 3),
                    'recall': round(recall, 3),
                    'n_samples': len(indices)
                }
            except Exception as e:
                logger.warning(f"Could not compute metrics for group {group}: {e}")
                continue
        
        # Find performance disparities
        disparities = []
        auc_scores = [(g, m['auc']) for g, m in subgroups.items()]
        
        if auc_scores:
            max_auc = max(auc_scores, key=lambda x: x[1])
            min_auc = min(auc_scores, key=lambda x: x[1])
            auc_gap = max_auc[1] - min_auc[1]
            
            if auc_gap > self.PERFORMANCE_DIFFERENTIAL_THRESHOLD:
                disparities.append({
                    'type': 'auc_disparity',
                    'best_group': max_auc[0],
                    'worst_group': min_auc[0],
                    'gap': round(auc_gap, 3),
                    'severity': 'HIGH' if auc_gap > 0.10 else 'MEDIUM'
                })
        
        return {
            'subgroup_performance': subgroups,
            'performance_disparities': disparities,
            'has_disparities': len(disparities) > 0
        }
    
    def analyze_decision_distribution(self, decisions: List[Dict]) -> Dict:
        """
        Analyze decision (approve/reject/hold) distribution by protected attributes.
        
        Returns:
            {
                'by_attribute': {
                    'gender': {group: {approved: int, rejected: int, held: int}},
                    'region': {...}
                }
            }
        """
        analysis = {'by_attribute': {}}
        
        for attr in self.PROTECTED_ATTRIBUTES:
            if attr == 'age':
                # Skip age for now (continuous)
                continue
            
            dist = {}
            for decision in decisions:
                group = decision.get(attr)
                if not group:
                    continue
                
                if group not in dist:
                    dist[group] = {'approved': 0, 'rejected': 0, 'held': 0}
                
                decision_type = decision.get('final_decision', 'unknown')
                if decision_type in dist[group]:
                    dist[group][decision_type] += 1
            
            analysis['by_attribute'][attr] = dist
        
        return analysis
    
    def generate_fairness_report(self, time_window_days: int = 30) -> Dict:
        """
        Generate comprehensive weekly fairness monitoring report.
        
        Args:
            time_window_days: Look back window (default 30 days)
        
        Returns:
            Full fairness report with all metrics and flags
        """
        if not self.db:
            logger.warning("No database connection for fairness report")
            return {}
        
        try:
            from app.models.models import LoanApplication, AuditLog, User
            
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            
            # Get recent decisions with user data
            applications = self.db.query(LoanApplication).join(
                User, LoanApplication.user_id == User.id
            ).filter(
                LoanApplication.created_at >= cutoff_date,
                LoanApplication.final_decision.isnot(None)
            ).all()
            
            if not applications:
                logger.warning("No applications in fairness window")
                return {'total_applications': 0, 'warning': 'Insufficient data'}
            
            # Convert to dicts for easier processing
            app_list = [
                {
                    'id': str(app.id),
                    'gender': getattr(app, 'gender', None),
                    'region': getattr(app, 'region', None),  # computed from location
                    'user_category': app.user.user_category.value if app.user and app.user.user_category else 'unknown',
                    'final_decision': app.final_decision.value if app.final_decision else None,
                    'probability_of_default': app.probability_of_default,
                    'credit_score': app.credit_score,
                    'created_at': app.created_at
                }
                for app in applications
            ]
            
            # Compute approval rates by gender
            approval_by_gender = self.compute_approval_rate_by_group(
                app_list, 'gender'
            )
            dir_gender = self.compute_disparate_impact_ratio(approval_by_gender)
            
            # Compute approval rates by user category
            approval_by_category = self.compute_approval_rate_by_group(
                app_list, 'user_category'
            )
            dir_category = self.compute_disparate_impact_ratio(approval_by_category)
            
            # Decision distribution analysis
            decision_dist = self.analyze_decision_distribution(app_list)
            
            # Summary metrics
            total_applications = len(app_list)
            approved_count = sum(1 for a in app_list if a['final_decision'] == 'approved')
            rejected_count = sum(1 for a in app_list if a['final_decision'] == 'rejected')
            held_count = sum(1 for a in app_list if a['final_decision'] == 'held')
            
            approval_rate = approved_count / total_applications if total_applications > 0 else 0
            avg_credit_score = np.mean([a['credit_score'] for a in app_list]) if app_list else 0
            avg_pd = np.mean([a['probability_of_default'] for a in app_list]) if app_list else 0
            
            # Compile overall risk assessment
            overall_bias_risk = 'LOW'
            if dir_gender['bias_detected'] or dir_category['bias_detected']:
                overall_bias_risk = 'HIGH'
            
            return {
                'report_date': datetime.utcnow().isoformat(),
                'time_window_days': time_window_days,
                'total_applications': total_applications,
                'decisions': {
                    'approved': approved_count,
                    'rejected': rejected_count,
                    'held': held_count,
                    'approval_rate': round(approval_rate, 3)
                },
                'model_metrics': {
                    'avg_credit_score': round(avg_credit_score, 1),
                    'avg_probability_of_default': round(avg_pd, 3)
                },
                'disparate_impact_by_gender': dir_gender,
                'disparate_impact_by_category': dir_category,
                'decision_distribution': decision_dist,
                'overall_bias_risk': overall_bias_risk,
                'flags': {
                    'gender_dir_flags': len(dir_gender['flags']),
                    'category_dir_flags': len(dir_category['flags']),
                    'requires_investigation': overall_bias_risk == 'HIGH'
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating fairness report: {e}")
            return {'error': str(e)}
    
    def flag_potentially_unfair_decision(self, application: Dict) -> Optional[Dict]:
        """
        Flag a single decision for potential unfairness (real-time checking).
        
        Returns:
            None if fair, or dict with concerns
        """
        flags = []
        
        # Check if credit score unusually low for this demographic
        # (This would require historical group means in DB)
        # Placeholder for future enhancement
        
        return flags if flags else None
