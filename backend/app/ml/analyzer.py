"""
SkyGuard AI - Master ML Analyzer Pipeline
Combines preprocessing, Isolation Forest, model feature attribution, temporal checks,
seasonal & diurnal baseline analysis, multivariate correlation, spatial consistency analysis,
diagnostic classification, explainable multi-evidence synthesis, and optional corrected value suggestions.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

from .preprocessor import preprocess_station_data, prepare_features_for_model
from .isolation_forest import SkyGuardIsolationForest
from .temporal_analyzer import TemporalAnalyzer
from .multivariate_analyzer import MultivariateAnalyzer
from .cause_classifier import CauseClassifier
from .feature_attribution import SkyGuardFeatureAttributor
from .spatial_analyzer import SpatialAnalyzer
from .seasonal_baseline import SeasonalBaselineLearner
from .value_corrector import ValueCorrector

logger = logging.getLogger(__name__)

class SkyGuardAnalyzer:
    def __init__(self, model_path: str = "./database/isolation_forest.pkl"):
        self.model_path = model_path
        self.if_model = SkyGuardIsolationForest.load_or_create(model_path)
        self.temporal = TemporalAnalyzer()
        self.seasonal = SeasonalBaselineLearner()
        self.multivariate = MultivariateAnalyzer()
        self.spatial = SpatialAnalyzer()
        self.classifier = CauseClassifier()
        self.corrector = ValueCorrector()

    def train(self, records: List[Dict[str, Any]], station_id: str = "AWS-001") -> bool:
        df = preprocess_station_data(records, station_id)
        if len(df) < 20:
            return False
        X, feature_names = prepare_features_for_model(df)
        if len(X) < 20:
            return False
        self.if_model.fit(X, feature_names)
        self.if_model.save(self.model_path)
        return True

    def analyze_reading(
        self,
        recent_records: List[Dict[str, Any]],
        station_id: str,
        latest_record: Dict[str, Any],
        neighbor_records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        all_records = recent_records + [latest_record]
        df = preprocess_station_data(all_records, station_id)

        if df.empty:
            return self._default_result(latest_record)

        anomaly_score = 0.0
        attribution_result = {
            "attribution_method": "Isolation Forest Decision Path Attribution",
            "model_feature_attribution_available": False,
            "feature_attributions": {},
            "top_contributing_features": []
        }

        if self.if_model.is_trained:
            try:
                X, feature_names = prepare_features_for_model(df)
                if len(X) > 0:
                    scores = self.if_model.predict_scores(X)
                    anomaly_score = float(scores[-1])

                    # Compute Model Feature Attributions for latest sample
                    attributor = SkyGuardFeatureAttributor(feature_names)
                    raw_vals = {col: float(df[col].iloc[-1]) for col in feature_names if col in df.columns}
                    attribution_result = attributor.explain_sample(
                        model=self.if_model.model,
                        scaler=self.if_model.scaler,
                        X_sample=X[-1:],
                        raw_feature_values=raw_vals
                    )
            except Exception as e:
                logger.error(f"IF scoring & feature attribution error: {e}")
                anomaly_score = 0.2

        temporal_findings = self.temporal.analyze(df)
        seasonal_result = self.seasonal.fit_and_evaluate(df, latest_record)
        mv_result = self.multivariate.analyze(df)
        spatial_result = self.spatial.analyze(latest_record, neighbor_records or [])

        missing = bool(latest_record.get('is_missing', False))
        comm_failure = False
        if len(df) >= 4 and 'is_missing' in df.columns:
            comm_failure = bool(df['is_missing'].tail(4).all())

        classification = self.classifier.classify(
            anomaly_score=anomaly_score,
            temporal_findings=temporal_findings,
            multivariate_result=mv_result,
            spatial_result=spatial_result,
            seasonal_result=seasonal_result,
            missing_data=missing,
            comm_failure=comm_failure
        )

        expected = {}
        for s in ['temperature', 'pressure', 'humidity']:
            if seasonal_result and seasonal_result.has_sufficient_history and s in seasonal_result.findings:
                expected[s] = seasonal_result.findings[s].expected_mean
            elif s in df.columns:
                col = f"{s}_roll_mean_short"
                if col in df.columns and len(df) > 1:
                    prev_val = df[col].iloc[-2] if len(df) > 1 else df[col].iloc[-1]
                    expected[s] = round(float(prev_val), 2) if not pd.isna(prev_val) else latest_record.get(s)
                else:
                    expected[s] = latest_record.get(s)
            else:
                expected[s] = latest_record.get(s)

        # Compute optional suggested corrected values
        corrected_values = self.corrector.suggest_corrections(
            classification=classification.classification,
            affected_sensor=classification.affected_sensor,
            latest_record=latest_record,
            recent_df=df,
            seasonal_result=seasonal_result,
            spatial_result=spatial_result
        )

        seasonal_dict = {
            "has_sufficient_history": seasonal_result.has_sufficient_history,
            "total_historical_samples": seasonal_result.total_historical_samples,
            "seasonal_anomaly_detected": seasonal_result.seasonal_anomaly_detected,
            "coherent_seasonal_shift": seasonal_result.coherent_seasonal_shift,
            "description": seasonal_result.description,
            "deviations": {
                k: {
                    "observed": v.observed,
                    "expected_mean": v.expected_mean,
                    "expected_range": list(v.expected_range),
                    "z_score": v.z_score,
                    "is_outlier": v.is_seasonal_outlier,
                    "context": v.context,
                    "description": v.description
                }
                for k, v in seasonal_result.findings.items()
            }
        }

        # Build clean, human-readable evidence summary
        explainable_evidence_summary = {
            "primary_contributor": attribution_result.get("primary_contributor", "Statistical Deviation"),
            "model_feature_attribution": attribution_result.get("explanation_summary", "Decision tree split analysis complete."),
            "temporal_findings": classification.evidence.get("temporal_evidence", {}).get("summary", "No temporal faults."),
            "spatial_corroboration": spatial_result.description if spatial_result else "No spatial peer data.",
            "seasonal_diurnal_context": seasonal_result.description if seasonal_result else "No seasonal baseline."
        }

        return {
            "anomaly_score": round(anomaly_score, 4),
            "anomaly_score_pct": round(anomaly_score * 100, 1),
            "is_anomaly": classification.classification != "NORMAL",
            "classification": classification.classification,
            "classification_label": classification.classification_label,
            "confidence": classification.confidence,
            "confidence_estimate_pct": round(classification.confidence * 100, 1),
            "confidence_pct": round(classification.confidence * 100, 1),
            "affected_sensor": classification.affected_sensor,
            "fault_type": classification.fault_type,
            "reason": classification.reason,
            "evidence": classification.evidence,
            "explainable_evidence": explainable_evidence_summary,
            "probable_cause": classification.probable_cause,
            "recommended_action": classification.recommended_action,
            "expected_temperature": expected.get('temperature'),
            "expected_pressure": expected.get('pressure'),
            "expected_humidity": expected.get('humidity'),
            "observed_temperature": latest_record.get('temperature'),
            "observed_pressure": latest_record.get('pressure'),
            "observed_humidity": latest_record.get('humidity'),
            "corrected_values": corrected_values,
            "corrected_temperature": corrected_values.get("temperature", {}).get("corrected_value"),
            "corrected_pressure": corrected_values.get("pressure", {}).get("corrected_value"),
            "corrected_humidity": corrected_values.get("humidity", {}).get("corrected_value"),
            "ai_expected_values": {
                "temperature": expected.get('temperature'),
                "pressure": expected.get('pressure'),
                "humidity": expected.get('humidity')
            },
            "feature_attribution": attribution_result,
            "shap_explanation": attribution_result,
            "seasonal_baseline": seasonal_dict,
            "spatial_consistency": {
                "detected": spatial_result.spatial_anomaly_detected,
                "regional_pattern": spatial_result.regional_pattern,
                "neighbor_count": spatial_result.neighbor_count,
                "temperature_delta": spatial_result.temperature_delta,
                "pressure_delta": spatial_result.pressure_delta,
                "humidity_delta": spatial_result.humidity_delta,
                "description": spatial_result.description
            },
            "multivariate": {
                "coherent_change": mv_result.coherent_change,
                "isolated_sensor": mv_result.isolated_sensor,
                "weather_event_likelihood": round(mv_result.weather_event_likelihood, 2),
                "sensor_fault_likelihood": round(mv_result.sensor_fault_likelihood, 2),
                "description": mv_result.description
            }
        }

    def _default_result(self, record: Dict[str, Any]) -> Dict[str, Any]:
        default_attr = {
            "attribution_method": "Empirical Baseline",
            "model_feature_attribution_available": False,
            "feature_attributions": {},
            "top_contributing_features": []
        }
        no_corr = {
            s: {
                "is_corrected": False,
                "status": "NO_CORRECTION_NEEDED",
                "method": "RAW_OBSERVATION_PRESERVED",
                "confidence": 1.0,
                "raw_value": record.get(s),
                "corrected_value": None,
                "is_estimated_optional": False,
                "explanation": "Nominal observation."
            }
            for s in ["temperature", "pressure", "humidity"]
        }
        return {
            "anomaly_score": 0.0,
            "anomaly_score_pct": 0.0,
            "is_anomaly": False,
            "classification": "NORMAL",
            "classification_label": "Normal Operations",
            "confidence": 0.95,
            "confidence_estimate_pct": 95.0,
            "confidence_pct": 95.0,
            "affected_sensor": None,
            "fault_type": None,
            "reason": "Baseline normal conditions.",
            "evidence": {},
            "explainable_evidence": {
                "primary_contributor": "Baseline",
                "model_feature_attribution": "Nominal operating envelope.",
                "temporal_findings": "No temporal faults.",
                "spatial_corroboration": "Nominal.",
                "seasonal_diurnal_context": "Nominal."
            },
            "probable_cause": "",
            "recommended_action": "Routine monitoring.",
            "expected_temperature": record.get('temperature'),
            "expected_pressure": record.get('pressure'),
            "expected_humidity": record.get('humidity'),
            "observed_temperature": record.get('temperature'),
            "observed_pressure": record.get('pressure'),
            "observed_humidity": record.get('humidity'),
            "corrected_values": no_corr,
            "corrected_temperature": None,
            "corrected_pressure": None,
            "corrected_humidity": None,
            "ai_expected_values": {
                "temperature": record.get('temperature'),
                "pressure": record.get('pressure'),
                "humidity": record.get('humidity')
            },
            "feature_attribution": default_attr,
            "shap_explanation": default_attr,
            "seasonal_baseline": {
                "has_sufficient_history": False,
                "total_historical_samples": 0,
                "seasonal_anomaly_detected": False,
                "coherent_seasonal_shift": False,
                "description": "Insufficient history."
            },
            "spatial_consistency": {"detected": False, "neighbor_count": 0, "description": "Spatially consistent."},
            "multivariate": {}
        }
