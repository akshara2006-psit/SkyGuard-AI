"""
SkyGuard AI - Isolation Forest Anomaly Detection Wrapper
"""
import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SkyGuardIsolationForest:
    def __init__(
        self,
        n_estimators: int = 150,
        contamination: float = 0.05,
        random_state: int = 42
    ):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names: List[str] = []
        self.training_score_min: float = -0.5
        self.training_score_max: float = 0.5

    def fit(self, X: np.ndarray, feature_names: Optional[List[str]] = None) -> 'SkyGuardIsolationForest':
        if len(X) == 0:
            return self
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        if feature_names:
            self.feature_names = feature_names

        raw_scores = self.model.score_samples(X_scaled)
        self.training_score_min = float(raw_scores.min())
        self.training_score_max = float(raw_scores.max())
        return self

    def predict_scores(self, X: np.ndarray) -> np.ndarray:
        """Normalized anomaly score between 0.0 (normal) and 1.0 (highly anomalous)."""
        if not self.is_trained:
            return np.zeros(len(X))
        X_scaled = self.scaler.transform(X)
        raw_scores = self.model.score_samples(X_scaled)
        score_range = self.training_score_max - self.training_score_min
        if score_range < 1e-6:
            score_range = 1.0
        # Invert: more negative score in Isolation Forest indicates higher anomaly
        normalized = (self.training_score_max - raw_scores) / score_range
        return np.clip(normalized, 0.0, 1.0)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_or_create(cls, path: str) -> 'SkyGuardIsolationForest':
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading model from {path}: {e}")
        return cls()
