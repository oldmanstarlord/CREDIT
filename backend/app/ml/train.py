"""
ML Model Training Pipeline
Trains XGBoost model with Optuna hyperparameter tuning and SHAP explainability
"""

import logging
import pandas as pd
import numpy as np
import pickle
import json
from typing import Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, accuracy_score
from imblearn.over_sampling import SMOTE
import optuna
from optuna.study import Study
import shap

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains and evaluates credit scoring model.
    Handles class imbalance, hyperparameter optimization, and SHAP explainability.
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = None
        self.shap_explainer = None
        self.feature_names = []
        self.test_metrics = {}
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None,
        optimize_hyperparams: bool = True,
        n_trials: int = 50
    ) -> 'ModelTrainer':
        """
        Train XGBoost model with optional hyperparameter optimization.
        
        Args:
            X_train: Training features
            y_train: Training labels (0=good, 1=default)
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            optimize_hyperparams: Run Optuna HPO if True
            n_trials: Number of Optuna trials
        
        Returns:
            Self for method chaining
        """
        self.feature_names = X_train.columns.tolist()
        
        # Split if no validation set provided
        if X_val is None:
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train, test_size=0.2, stratify=y_train,
                random_state=self.random_state
            )
        
        # Handle class imbalance: Compare SMOTE vs class_weight
        logger.info("Evaluating imbalance handling strategies...")
        auc_smote = self._train_with_smote(X_train, y_train, X_val, y_val)
        auc_weighted = self._train_with_class_weight(X_train, y_train, X_val, y_val)
        
        logger.info(f"SMOTE AUC: {auc_smote:.4f} | Class Weight AUC: {auc_weighted:.4f}")
        use_smote = auc_smote > auc_weighted
        
        # Hyperparameter optimization
        if optimize_hyperparams:
            logger.info("Running Optuna hyperparameter optimization...")
            best_params = self._optimize_hyperparams(
                X_train, y_train, X_val, y_val,
                use_smote=use_smote,
                n_trials=n_trials
            )
        else:
            best_params = self._get_default_hyperparams()
        
        # Train final model
        logger.info("Training final model with best hyperparameters...")
        self.model = self._train_xgboost(
            X_train, y_train, X_val, y_val,
            best_params, use_smote=use_smote
        )
        
        # Initialize SHAP explainer
        logger.info("Initializing SHAP explainer...")
        self.shap_explainer = shap.TreeExplainer(self.model)
        
        return self
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series,
                 threshold: float = 0.35) -> Dict:
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test labels
            threshold: Decision threshold for classification
        
        Returns:
            Dictionary of evaluation metrics
        """
        probs = self.model.predict_proba(X_test)[:, 1]
        preds = (probs >= threshold).astype(int)
        
        metrics = {
            'auc_roc': roc_auc_score(y_test, probs),
            'accuracy': accuracy_score(y_test, preds),
            'precision': precision_score(y_test, preds, zero_division=0),
            'recall': recall_score(y_test, preds, zero_division=0),
            'f1_score': f1_score(y_test, preds, zero_division=0),
            'threshold': threshold
        }
        
        self.test_metrics = metrics
        
        logger.info(f"Test metrics: {json.dumps(metrics, indent=2)}")
        
        return metrics
    
    def tune_decision_threshold(self, X_val: pd.DataFrame, 
                                y_val: pd.Series) -> float:
        """
        Find optimal decision threshold for credit decisions.
        Balances false positives (reject good borrowers) vs false negatives (approve bad borrowers).
        
        Args:
            X_val: Validation features
            y_val: Validation labels
        
        Returns:
            Optimal threshold
        """
        probs = self.model.predict_proba(X_val)[:, 1]
        thresholds = np.arange(0.20, 0.70, 0.01)
        best_threshold = 0.35
        best_score = 0
        
        for t in thresholds:
            preds = (probs >= t).astype(int)
            # Weight recall higher - missing a defaulter is more costly
            score = f1_score(y_val, preds, pos_label=1)
            
            if score > best_score:
                best_score = score
                best_threshold = t
        
        logger.info(f"Optimal threshold: {best_threshold:.3f} (F1: {best_score:.4f})")
        
        return best_threshold
    
    def explain_prediction(self, x: np.ndarray, top_n: int = 10) -> Dict:
        """
        Generate SHAP explanation for single prediction.
        
        Args:
            x: Single sample (1D array)
            top_n: Number of top factors to return
        
        Returns:
            SHAP explanation dictionary
        """
        shap_values = self.shap_explainer.shap_values(x.reshape(1, -1))[0]
        
        # Get top factors
        indexed = list(zip(self.feature_names, shap_values))
        
        top_positive = sorted(
            indexed, key=lambda x: x[1], reverse=True
        )[:top_n]
        top_negative = sorted(
            indexed, key=lambda x: x[1]
        )[:top_n]
        
        return {
            'base_value': float(self.shap_explainer.expected_value),
            'shap_values': dict(zip(self.feature_names, shap_values)),
            'top_positive_factors': [(name, float(val)) for name, val in top_positive],
            'top_negative_factors': [(name, float(val)) for name, val in top_negative]
        }
    
    def save(self, model_path: str, explainer_path: str = None):
        """
        Save trained model and explainer.
        
        Args:
            model_path: Path to save XGBoost model
            explainer_path: Path to save SHAP explainer
        """
        self.model.save_model(model_path)
        logger.info(f"Model saved to {model_path}")
        
        if explainer_path and self.shap_explainer:
            with open(explainer_path, 'wb') as f:
                pickle.dump(self.shap_explainer, f)
            logger.info(f"SHAP explainer saved to {explainer_path}")
    
    def _train_with_smote(self, X_train, y_train, X_val, y_val) -> float:
        """Train with SMOTE and return AUC"""
        smote = SMOTE(random_state=self.random_state, sampling_strategy='auto')
        X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
        
        model = xgb.XGBClassifier(
            eval_metric='auc',
            use_label_encoder=False,
            random_state=self.random_state,
            n_jobs=-1
        )
        model.fit(X_train_smote, y_train_smote)
        
        probs = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, probs)
    
    def _train_with_class_weight(self, X_train, y_train, X_val, y_val) -> float:
        """Train with class weights and return AUC"""
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        
        model = xgb.XGBClassifier(
            eval_metric='auc',
            use_label_encoder=False,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_state,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        probs = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, probs)
    
    def _optimize_hyperparams(
        self, X_train, y_train, X_val, y_val,
        use_smote: bool, n_trials: int
    ) -> Dict:
        """Run Optuna hyperparameter optimization"""
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 8),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'gamma': trial.suggest_float('gamma', 0.0, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
            }
            
            X_train_subset = X_train
            y_train_subset = y_train
            
            if use_smote:
                smote = SMOTE(random_state=self.random_state)
                X_train_subset, y_train_subset = smote.fit_resample(X_train, y_train)
            
            model = xgb.XGBClassifier(
                **params,
                eval_metric='auc',
                use_label_encoder=False,
                random_state=self.random_state,
                n_jobs=-1
            )
            
            model.fit(X_train_subset, y_train_subset)
            probs = model.predict_proba(X_val)[:, 1]
            
            return roc_auc_score(y_val, probs)
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        logger.info(f"Best trial: {study.best_trial}")
        
        return study.best_params
    
    @staticmethod
    def _get_default_hyperparams() -> Dict:
        """Default XGBoost hyperparameters"""
        return {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 1,
            'gamma': 0.0,
            'reg_alpha': 0.5,
            'reg_lambda': 1.0
        }
    
    @staticmethod
    def _train_xgboost(X_train, y_train, X_val, y_val, params: Dict,
                       use_smote: bool) -> xgb.XGBClassifier:
        """Train final XGBoost model"""
        
        if use_smote:
            smote = SMOTE(random_state=42)
            X_train, y_train = smote.fit_resample(X_train, y_train)
        
        model = xgb.XGBClassifier(
            **params,
            eval_metric='auc',
            use_label_encoder=False,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        return model
