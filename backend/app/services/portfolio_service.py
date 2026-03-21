"""
Portfolio risk engine: Monte Carlo simulation for credit portfolio risk assessment.

Simulates potential loss scenarios across the loan portfolio and computes
Value-at-Risk (VaR), Conditional VaR (CVaR), and concentration risk metrics.
"""

from typing import Dict, List, Tuple, Optional
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Loan:
    """Represents a single loan in the portfolio"""
    loan_id: str
    amount: float  # Loan amount in INR
    pd: float  # Probability of default (0-1)
    lgd: float  # Loss given default (0-1), typically 0.4-0.6 for unsecured
    user_category: str
    issued_date: datetime
    
    def expected_loss(self) -> float:
        """Expected loss for this loan"""
        return self.amount * self.pd * self.lgd


class MonteCarloPortfolioSimulator:
    """
    Simulates portfolio-level credit risk using Monte Carlo method.
    
    Run 10,000 simulations of potential default scenarios to understand
    tail risk (VaR @ 95%, 99%) and portfolio concentration.
    """
    
    # Recovery rate assumptions by collateral type
    LGD_BY_CATEGORY = {
        'farmer': 0.50,              # 50% loss if farmer defaults (land has value)
        'daily_wage_worker': 0.70,   # 70% loss (minimal collateral)
        'gig_worker': 0.65,          # 65% loss (vehicle sometimes present)
        'msme_owner': 0.45,          # 45% loss (business assets)
        'homemaker': 0.40,           # 40% loss (guaranteed by spouse)
        'low_income_salaried': 0.60, # 60% loss (salary garnishing possible)
    }
    
    def __init__(self, portfolio: List[Dict], n_simulations: int = 10000,
                 correlation_matrix: Optional[np.ndarray] = None):
        """
        Initialize portfolio simulator.
        
        Args:
            portfolio: List of loan dicts with 'amount', 'pd', 'user_category', etc.
            n_simulations: Number of Monte Carlo draws
            correlation_matrix: Optional correlation between defaults (for systemic risk)
        """
        self.portfolio = [
            Loan(
                loan_id=loan.get('id', str(i)),
                amount=float(loan.get('amount', 100000)),
                pd=float(loan.get('probability_of_default', 0.2)),
                lgd=float(loan.get('lgd', self.LGD_BY_CATEGORY.get(
                    loan.get('user_category'), 0.6))),
                user_category=loan.get('user_category', 'unknown'),
                issued_date=loan.get('issued_date', datetime.utcnow())
            )
            for i, loan in enumerate(portfolio)
        ]
        
        self.n_simulations = n_simulations
        self.correlation_matrix = correlation_matrix
        self.total_exposure = sum(loan.amount for loan in self.portfolio)
        
        logger.info(f"Portfolio initialized: {len(self.portfolio)} loans, "
                   f"Total exposure: ₹{self.total_exposure:,.0f}")
    
    def simulate(self) -> Dict:
        """
        Run Monte Carlo simulation of portfolio defaults.
        
        Returns:
            {
                'expected_loss': float,
                'var_95': float,
                'var_99': float,
                'cvar_95': float,
                'cvar_99': float,
                'max_loss': float,
                'loss_distribution': [losses from all simulations],
                'probability_of_zero_loss': float,
                'confidence_intervals': {95: (lower, upper), 99: (lower, upper)}
            }
        """
        losses = []
        zero_loss_count = 0
        
        for sim in range(self.n_simulations):
            if sim % 1000 == 0:
                logger.debug(f"Simulation {sim}/{self.n_simulations}")
            
            simulation_loss = 0.0
            
            for loan in self.portfolio:
                # Generate default probability draw
                # Using Bernoulli distribution: default occurs with prob = pd
                default_occurred = np.random.random() < loan.pd
                
                if default_occurred:
                    # Loss = Amount × LGD
                    # Adding 10% randomness to LGD to account for recovery uncertainty
                    lgd_adjusted = loan.lgd * np.random.normal(1.0, 0.1)
                    lgd_adjusted = np.clip(lgd_adjusted, 0, 1)
                    loss = loan.amount * lgd_adjusted
                    simulation_loss += loss
            
            if simulation_loss == 0:
                zero_loss_count += 1
            
            losses.append(simulation_loss)
        
        losses = np.array(losses)
        
        # Compute risk metrics
        expected_loss = float(np.mean(losses))
        expected_loss_pct = expected_loss / self.total_exposure if self.total_exposure else 0
        
        var_95 = float(np.percentile(losses, 95))
        var_99 = float(np.percentile(losses, 99))
        
        # Conditional VaR = mean of losses exceeding VaR threshold
        losses_exceeding_95 = losses[losses >= np.percentile(losses, 95)]
        cvar_95 = float(np.mean(losses_exceeding_95)) if len(losses_exceeding_95) > 0 else var_95
        
        losses_exceeding_99 = losses[losses >= np.percentile(losses, 99)]
        cvar_99 = float(np.mean(losses_exceeding_99)) if len(losses_exceeding_99) > 0 else var_99
        
        # Confidence intervals
        ci_95_lower = float(np.percentile(losses, 2.5))
        ci_95_upper = float(np.percentile(losses, 97.5))
        ci_99_lower = float(np.percentile(losses, 0.5))
        ci_99_upper = float(np.percentile(losses, 99.5))
        
        return {
            'expected_loss_inr': round(expected_loss, 0),
            'expected_loss_pct': round(expected_loss_pct * 100, 2),
            'var_95_inr': round(var_95, 0),
            'var_95_pct': round(var_95 / self.total_exposure * 100, 2) if self.total_exposure else 0,
            'var_99_inr': round(var_99, 0),
            'var_99_pct': round(var_99 / self.total_exposure * 100, 2) if self.total_exposure else 0,
            'cvar_95_inr': round(cvar_95, 0),
            'cvar_95_pct': round(cvar_95 / self.total_exposure * 100, 2) if self.total_exposure else 0,
            'cvar_99_inr': round(cvar_99, 0),
            'cvar_99_pct': round(cvar_99 / self.total_exposure * 100, 2) if self.total_exposure else 0,
            'max_simulated_loss_inr': round(float(np.max(losses)), 0),
            'min_simulated_loss_inr': round(float(np.min(losses)), 0),
            'probability_of_zero_loss': round(zero_loss_count / self.n_simulations, 4),
            'confidence_intervals': {
                95: (round(ci_95_lower, 0), round(ci_95_upper, 0)),
                99: (round(ci_99_lower, 0), round(ci_99_upper, 0))
            },
            'loss_distribution_percentiles': {
                '10th': float(np.percentile(losses, 10)),
                '25th': float(np.percentile(losses, 25)),
                '50th': float(np.percentile(losses, 50)),  # median
                '75th': float(np.percentile(losses, 75)),
                '90th': float(np.percentile(losses, 90))
            },
            'n_simulations': self.n_simulations
        }
    
    def compute_portfolio_statistics(self) -> Dict:
        """
        Compute basic portfolio statistics (weighted average PD, LGD, etc.)
        
        Returns:
            {
                'avg_pd': float,
                'avg_pd_by_category': dict,
                'avg_lgd': float,
                'portfolio_concentration': dict,
                'total_exposure': float
            }
        """
        # Weighted average PD
        avg_pd = sum(loan.pd * loan.amount for loan in self.portfolio) / self.total_exposure \
                 if self.total_exposure else 0
        
        # Average LGD
        avg_lgd = sum(loan.lgd * loan.amount for loan in self.portfolio) / self.total_exposure \
                  if self.total_exposure else 0
        
        # By category
        by_category = {}
        for loan in self.portfolio:
            if loan.user_category not in by_category:
                by_category[loan.user_category] = {'amount': 0, 'count': 0, 'pd_sum': 0}
            
            by_category[loan.user_category]['amount'] += loan.amount
            by_category[loan.user_category]['count'] += 1
            by_category[loan.user_category]['pd_sum'] += loan.pd * loan.amount
        
        category_stats = {}
        for cat, data in by_category.items():
            avg_cat_pd = data['pd_sum'] / data['amount'] if data['amount'] > 0 else 0
            pct_of_portfolio = data['amount'] / self.total_exposure * 100 if self.total_exposure else 0
            category_stats[cat] = {
                'exposure_inr': int(data['amount']),
                'pct_of_portfolio': round(pct_of_portfolio, 1),
                'count': data['count'],
                'avg_pd': round(avg_cat_pd, 4),
                'concentration_risk': 'HIGH' if pct_of_portfolio > 40 else 'MEDIUM' if pct_of_portfolio > 20 else 'LOW'
            }
        
        return {
            'total_exposure_inr': int(self.total_exposure),
            'num_loans': len(self.portfolio),
            'avg_loan_size_inr': int(self.total_exposure / len(self.portfolio)) if self.portfolio else 0,
            'portfolio_pd': round(avg_pd, 4),
            'portfolio_lgd': round(avg_lgd, 4),
            'portfolio_ead': round(self.total_exposure, 0),  # Exposure at Default
            'by_category': category_stats,
            'concentration_risk': 'HIGH' if max((s.get('pct_of_portfolio', 0) 
                                                  for s in category_stats.values()), default=0) > 40 
                                   else 'LOW'
        }
    
    def identify_concentration_risk(self) -> Dict:
        """
        Identify portfolio concentration risk.
        Flag if any single category dominates > 40% of portfolio.
        
        Returns:
            {
                'concentration_by_category': {cat: pct},
                'concentration_by_income_level': {...},
                'risk_assessment': 'HIGH' | 'MEDIUM' | 'LOW',
                'recommendations': [...]
            }
        """
        concentration_by_category = {}
        for loan in self.portfolio:
            cat = loan.user_category
            if cat not in concentration_by_category:
                concentration_by_category[cat] = 0
            concentration_by_category[cat] += loan.amount
        
        # Convert to percentages
        concentration_by_category = {
            cat: round(amt / self.total_exposure * 100, 1)
            for cat, amt in concentration_by_category.items()
        }
        
        max_concentration = max(concentration_by_category.values(), default=0)
        
        # Risk assessment
        if max_concentration > 40:
            risk_level = 'HIGH'
        elif max_concentration > 25:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Recommendations
        recommendations = []
        for cat, pct in concentration_by_category.items():
            if pct > 40:
                recommendations.append(
                    f"Reduce {cat} concentration from {pct}% to <25%"
                )
        
        return {
            'concentration_by_category': concentration_by_category,
            'max_concentration_pct': max_concentration,
            'risk_assessment': risk_level,
            'recommendations': recommendations
        }
    
    def compute_default_correlation_matrix(self) -> np.ndarray:
        """
        Estimate default correlations between loans (for systemic risk modeling).
        
        Currently uses category-based correlation assumption:
        - Same category: 0.3 correlation
        - Different category: 0.1 correlation
        - Same applicant: 0.9 correlation (not possible in practice)
        
        Returns:
            N×N default correlation matrix
        """
        n = len(self.portfolio)
        corr = np.ones((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                if self.portfolio[i].user_category == self.portfolio[j].user_category:
                    corr[i, j] = corr[j, i] = 0.3  # Same category: moderate correlation
                else:
                    corr[i, j] = corr[j, i] = 0.1  # Different category: low correlation
        
        return corr
    
    def stress_test(self, stress_scenario: str) -> Dict:
        """
        Run stress test under adverse scenario.
        
        Scenarios:
        - 'economic_downturn': All PDs increase by 50%
        - 'sector_shock': Category-specific PD increase (farmer: +80%, others: +30%)
        - 'systemic_crash': All PDs increase by 100%, perfect correlation
        
        Returns:
            Stress test results with potential losses
        """
        # Create stressed version of portfolio
        stressed_portfolio = []
        
        for loan in self.portfolio:
            stressed_loan = Loan(
                loan_id=loan.loan_id,
                amount=loan.amount,
                pd=loan.pd,  # Will adjust below
                lgd=loan.lgd,
                user_category=loan.user_category,
                issued_date=loan.issued_date
            )
            
            if stress_scenario == 'economic_downturn':
                stressed_loan.pd = min(0.99, loan.pd * 1.5)
            elif stress_scenario == 'sector_shock':
                if loan.user_category == 'farmer':
                    stressed_loan.pd = min(0.99, loan.pd * 1.8)
                else:
                    stressed_loan.pd = min(0.99, loan.pd * 1.3)
            elif stress_scenario == 'systemic_crash':
                stressed_loan.pd = min(0.99, loan.pd * 2.0)
            
            stressed_portfolio.append(stressed_loan)
        
        # Temporarily replace portfolio and run simulation
        original_portfolio = self.portfolio
        self.portfolio = stressed_portfolio
        
        stressed_results = self.simulate()
        
        self.portfolio = original_portfolio
        
        return {
            'scenario': stress_scenario,
            'stressed_results': stressed_results,
            'vs_baseline': {
                'expected_loss_increase_pct': round(
                    (stressed_results['expected_loss_inr'] - self.simulate()['expected_loss_inr']) / 
                    self.simulate()['expected_loss_inr'] * 100 if self.simulate()['expected_loss_inr'] > 0 else 0,
                    1
                )
            }
        }
