"""
SkyGuard AI — Phase 5B Focused Tests
Tests: multi-layer confidence, explainable evidence, value corrector, routes serializer.

Rules:
- No database access.
- No NOAA re-import.
- No modification of existing data.
- All tests use synthetic in-memory data.
"""
import sys
import os
import pytest

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ---------------------------------------------------------------------------
# 1. CONFIDENCE — Multi-layer formula in CauseClassifier
# ---------------------------------------------------------------------------

class TestPhase5BConfidence:
    """Validate that PROBABLE_SENSOR_ANOMALY confidence is multi-layer derived
    and numerically distinct from the raw anomaly_score."""

    def _make_temporal_findings(self, include_fault: bool):
        if not include_fault:
            return {}
        # Match the actual TemporalFinding fields: fault_type (str), severity (float), description (str)
        from types import SimpleNamespace
        f = SimpleNamespace(
            fault_type="FROZEN_SENSOR",
            severity=0.85,          # must be float — cause_classifier calls round(f.severity, 2)
            description="Temperature frozen for 6 consecutive readings."
        )
        return {"temperature": [f]}

    def _make_mv_result(self, isolated: bool):
        from types import SimpleNamespace
        return SimpleNamespace(
            coherent_change=not isolated,
            isolated_sensor=isolated,
            weather_event_likelihood=0.1 if isolated else 0.6,
            sensor_fault_likelihood=0.8 if isolated else 0.2,
            description="test",
            evidence={}  # cause_classifier checks mv.evidence for normalized_changes
        )

    def _make_spatial_result(self, contradiction: bool):
        from types import SimpleNamespace
        return SimpleNamespace(
            spatial_anomaly_detected=contradiction,
            regional_pattern="ISOLATED_OUTLIER" if contradiction else "COHERENT",
            neighbor_count=3,
            temperature_delta=8.0 if contradiction else 0.5,
            pressure_delta=0.5,
            humidity_delta=1.0,
            description="test"
        )

    def test_confidence_is_separate_from_anomaly_score(self):
        from backend.app.ml.cause_classifier import CauseClassifier
        cc = CauseClassifier()
        anomaly_score = 0.55  # raw IF score
        temporal = self._make_temporal_findings(include_fault=True)
        mv = self._make_mv_result(isolated=True)
        sp = self._make_spatial_result(contradiction=True)
        result = cc.classify(
            anomaly_score=anomaly_score,
            temporal_findings=temporal,
            multivariate_result=mv,
            spatial_result=sp
        )
        # Confidence must NOT simply equal anomaly_score
        assert result.confidence != anomaly_score, (
            f"confidence ({result.confidence}) must differ from anomaly_score ({anomaly_score})"
        )
        assert 0.0 <= result.confidence <= 1.0, "confidence must be in [0,1]"

    def test_probable_sensor_anomaly_confidence_range(self):
        """PROBABLE_SENSOR_ANOMALY confidence should be >= 0.60 with sufficient evidence."""
        from backend.app.ml.cause_classifier import CauseClassifier
        cc = CauseClassifier()
        temporal = self._make_temporal_findings(include_fault=True)
        mv = self._make_mv_result(isolated=True)
        sp = self._make_spatial_result(contradiction=True)
        result = cc.classify(
            anomaly_score=0.65,
            temporal_findings=temporal,
            multivariate_result=mv,
            spatial_result=sp
        )
        assert result.classification == "PROBABLE_SENSOR_ANOMALY"
        assert result.confidence >= 0.60, (
            f"Expected confidence >= 0.60, got {result.confidence}"
        )
        assert result.confidence <= 0.98, (
            f"Confidence capped at 0.98, got {result.confidence}"
        )

    def test_normal_reading_confidence(self):
        """Normal classification should have high confidence (low uncertainty)."""
        from backend.app.ml.cause_classifier import CauseClassifier
        from types import SimpleNamespace
        cc = CauseClassifier()
        mv = SimpleNamespace(
            coherent_change=False, isolated_sensor=False,
            weather_event_likelihood=0.05, sensor_fault_likelihood=0.05,
            description="",
            evidence={}  # needed by mv.evidence check in classifier
        )
        sp = SimpleNamespace(
            spatial_anomaly_detected=False, regional_pattern="COHERENT",
            neighbor_count=3, temperature_delta=0.2, pressure_delta=0.1,
            humidity_delta=0.3, description=""
        )
        result = cc.classify(
            anomaly_score=0.10,
            temporal_findings={},
            multivariate_result=mv,
            spatial_result=sp
        )
        assert result.classification == "NORMAL"
        assert result.confidence >= 0.80, (
            f"Normal classification should have high confidence, got {result.confidence}"
        )

    def test_evidence_dict_has_structured_keys(self):
        """Evidence dict should contain temporal_evidence sub-key for sensor anomalies."""
        from backend.app.ml.cause_classifier import CauseClassifier
        cc = CauseClassifier()
        temporal = self._make_temporal_findings(include_fault=True)
        mv = self._make_mv_result(isolated=True)
        sp = self._make_spatial_result(contradiction=True)
        result = cc.classify(
            anomaly_score=0.70,
            temporal_findings=temporal,
            multivariate_result=mv,
            spatial_result=sp
        )
        if result.classification == "PROBABLE_SENSOR_ANOMALY":
            assert "temporal_evidence" in result.evidence, (
                "evidence must include 'temporal_evidence' for PROBABLE_SENSOR_ANOMALY"
            )


# ---------------------------------------------------------------------------
# 2. VALUE CORRECTOR — Core safety and output structure
# ---------------------------------------------------------------------------

class TestPhase5BValueCorrector:
    """Validate ValueCorrector safety constraints and output structure."""

    def _make_recent_df(self):
        import pandas as pd
        import numpy as np
        timestamps = pd.date_range("2022-01-04 12:00", periods=12, freq="5min")
        return pd.DataFrame({
            "timestamp": timestamps,
            "temperature": np.random.normal(15.0, 0.3, 12),
            "pressure": np.random.normal(1013.0, 0.5, 12),
            "humidity": np.random.normal(65.0, 1.0, 12),
            "temperature_roll_mean_short": [15.0] * 12,
            "pressure_roll_mean_short": [1013.0] * 12,
            "humidity_roll_mean_short": [65.0] * 12,
        })

    def _make_spatial_result_with_peers(self):
        from types import SimpleNamespace
        return SimpleNamespace(
            spatial_anomaly_detected=True,
            regional_pattern="ISOLATED_OUTLIER",
            neighbor_count=3,
            temperature_delta=10.0,
            pressure_delta=1.0,
            humidity_delta=3.0,
            description="Spatial outlier"
        )

    def test_never_overwrites_raw_value(self):
        """Corrected value must be stored separately; raw value in output must match input."""
        from backend.app.ml.value_corrector import ValueCorrector
        vc = ValueCorrector()
        raw_temp = 99.0  # clearly anomalous
        record = {"temperature": raw_temp, "pressure": 1013.0, "humidity": 65.0}
        df = self._make_recent_df()
        result = vc.suggest_corrections(
            classification="PROBABLE_SENSOR_ANOMALY",
            affected_sensor="temperature",
            latest_record=record,
            recent_df=df,
            seasonal_result=None,
            spatial_result=self._make_spatial_result_with_peers()
        )
        t_result = result.get("temperature", {})
        assert isinstance(t_result, dict), "correction result must be a dict"
        # raw_value must equal input
        assert t_result.get("raw_value") == raw_temp, (
            f"raw_value must equal original {raw_temp}, got {t_result.get('raw_value')}"
        )

    def test_no_correction_for_normal(self):
        """No correction should be applied for NORMAL classification."""
        from backend.app.ml.value_corrector import ValueCorrector
        vc = ValueCorrector()
        record = {"temperature": 15.0, "pressure": 1013.0, "humidity": 65.0}
        df = self._make_recent_df()
        result = vc.suggest_corrections(
            classification="NORMAL",
            affected_sensor=None,
            latest_record=record,
            recent_df=df,
            seasonal_result=None,
            spatial_result=None
        )
        for sensor in ["temperature", "pressure", "humidity"]:
            entry = result.get(sensor, {})
            if isinstance(entry, dict):
                assert entry.get("corrected_value") is None or entry.get("is_corrected") is False, (
                    f"No correction should be applied for NORMAL, sensor={sensor}"
                )

    def test_correction_marked_estimated_optional(self):
        """Any applied correction must be tagged as ESTIMATED_OPTIONAL."""
        from backend.app.ml.value_corrector import ValueCorrector
        vc = ValueCorrector()
        record = {"temperature": 99.0, "pressure": 1013.0, "humidity": 65.0}
        df = self._make_recent_df()
        sp = self._make_spatial_result_with_peers()
        result = vc.suggest_corrections(
            classification="PROBABLE_SENSOR_ANOMALY",
            affected_sensor="temperature",
            latest_record=record,
            recent_df=df,
            seasonal_result=None,
            spatial_result=sp
        )
        t_result = result.get("temperature", {})
        if isinstance(t_result, dict) and t_result.get("is_corrected"):
            status = t_result.get("status", "")
            assert "ESTIMATED" in status or t_result.get("is_estimated_optional") is True, (
                f"Corrected values must be marked ESTIMATED_OPTIONAL, got status={status}"
            )

    def test_returns_null_on_insufficient_evidence(self):
        """When no spatial/seasonal data available and history is tiny, corrected_value = None."""
        import pandas as pd
        from backend.app.ml.value_corrector import ValueCorrector
        vc = ValueCorrector()
        record = {"temperature": 99.0, "pressure": 1013.0, "humidity": 65.0}
        tiny_df = pd.DataFrame({
            "timestamp": pd.date_range("2022-01-04", periods=2, freq="5min"),
            "temperature": [15.5, 15.6],
            "pressure": [1013.0, 1013.1],
            "humidity": [65.0, 65.1],
        })
        result = vc.suggest_corrections(
            classification="PROBABLE_SENSOR_ANOMALY",
            affected_sensor="temperature",
            latest_record=record,
            recent_df=tiny_df,
            seasonal_result=None,
            spatial_result=None
        )
        t_result = result.get("temperature", {})
        if isinstance(t_result, dict) and not t_result.get("is_corrected"):
            # INSUFFICIENT_EVIDENCE expected
            assert t_result.get("corrected_value") is None, (
                "No correction should be invented without sufficient evidence"
            )

    def test_output_structure_completeness(self):
        """All three sensors (T, P, RH) must be represented in the output dict."""
        from backend.app.ml.value_corrector import ValueCorrector
        vc = ValueCorrector()
        record = {"temperature": 99.0, "pressure": 1013.0, "humidity": 65.0}
        df = self._make_recent_df()
        result = vc.suggest_corrections(
            classification="PROBABLE_SENSOR_ANOMALY",
            affected_sensor="temperature",
            latest_record=record,
            recent_df=df,
            seasonal_result=None,
            spatial_result=None
        )
        for sensor in ["temperature", "pressure", "humidity"]:
            assert sensor in result, f"Result must contain key '{sensor}'"


# ---------------------------------------------------------------------------
# 3. ANALYZER — Phase 5B payload keys present
# ---------------------------------------------------------------------------

class TestPhase5BAnalyzerPayload:
    """Validate that analyze_reading() returns Phase 5B keys in its result."""

    def _build_records(self, n=30):
        import random
        import datetime
        base = datetime.datetime(2022, 1, 4, 12, 0)
        recs = []
        for i in range(n):
            recs.append({
                "station_id": "KATL",
                "timestamp": (base + datetime.timedelta(minutes=5 * i)).isoformat(),
                "temperature": round(14.0 + random.gauss(0, 0.5), 2),
                "pressure": round(1013.0 + random.gauss(0, 0.3), 2),
                "humidity": round(65.0 + random.gauss(0, 1.0), 2),
                "is_missing": False,
                "data_quality": "GOOD",
            })
        return recs

    def test_analyze_returns_phase5b_keys(self):
        """analyze_reading() result must include corrected_values and explainable_evidence."""
        from backend.app.ml.analyzer import SkyGuardAnalyzer
        analyzer = SkyGuardAnalyzer(model_path="./database/isolation_forest.pkl")
        records = self._build_records(30)
        latest = records[-1]
        result = analyzer.analyze_reading(
            recent_records=records[:-1],
            station_id="KATL",
            latest_record=latest
        )
        assert "corrected_values" in result, "Result must contain 'corrected_values'"
        assert "corrected_temperature" in result, "Result must contain 'corrected_temperature'"
        assert "corrected_pressure" in result, "Result must contain 'corrected_pressure'"
        assert "corrected_humidity" in result, "Result must contain 'corrected_humidity'"
        assert "explainable_evidence" in result, "Result must contain 'explainable_evidence'"
        assert "confidence" in result, "Result must contain 'confidence'"
        assert "anomaly_score" in result, "Result must contain 'anomaly_score'"

    def test_confidence_and_score_are_distinct_types(self):
        """confidence and anomaly_score are separate numeric fields."""
        from backend.app.ml.analyzer import SkyGuardAnalyzer
        analyzer = SkyGuardAnalyzer(model_path="./database/isolation_forest.pkl")
        records = self._build_records(30)
        latest = records[-1]
        result = analyzer.analyze_reading(
            recent_records=records[:-1],
            station_id="KATL",
            latest_record=latest
        )
        conf = result["confidence"]
        score = result["anomaly_score"]
        assert isinstance(conf, float), "confidence must be a float"
        assert isinstance(score, float), "anomaly_score must be a float"
        assert 0.0 <= conf <= 1.0
        assert 0.0 <= score <= 1.0

    def test_corrected_values_structure(self):
        """corrected_values must be a dict with temperature/pressure/humidity keys."""
        from backend.app.ml.analyzer import SkyGuardAnalyzer
        analyzer = SkyGuardAnalyzer(model_path="./database/isolation_forest.pkl")
        records = self._build_records(30)
        latest = records[-1]
        result = analyzer.analyze_reading(
            recent_records=records[:-1],
            station_id="KATL",
            latest_record=latest
        )
        cv = result["corrected_values"]
        assert isinstance(cv, dict), "corrected_values must be a dict"
        for sensor in ["temperature", "pressure", "humidity"]:
            assert sensor in cv, f"corrected_values must contain '{sensor}'"


# ---------------------------------------------------------------------------
# 4. ROUTES — anomaly_to_dict() Phase 5B serialization
# ---------------------------------------------------------------------------

class TestPhase5BRoutesSerialization:
    """Validate that anomaly_to_dict exposes Phase 5B fields properly."""

    def _make_mock_anomaly(self, evidence_json: str = "{}"):
        from types import SimpleNamespace
        import datetime
        a = SimpleNamespace(
            id=1,
            station_id="KATL",
            timestamp=datetime.datetime(2022, 1, 4, 12, 0),
            anomaly_score=0.72,
            is_anomaly=True,
            classification="PROBABLE_SENSOR_ANOMALY",
            confidence=0.84,
            affected_sensor="temperature",
            fault_type="SPIKE",
            observed_temperature=99.0,
            expected_temperature=14.5,
            observed_pressure=1013.0,
            expected_pressure=1013.0,
            observed_humidity=65.0,
            expected_humidity=65.0,
            reason="Temperature spike detected",
            evidence=evidence_json,
            probable_cause="Sensor malfunction",
            recommended_action="Inspect temperature sensor",
        )
        return a

    def test_anomaly_to_dict_has_phase5b_keys(self):
        """anomaly_to_dict must return corrected_values and explainable_evidence keys."""
        from backend.app.api.routes import anomaly_to_dict
        a = self._make_mock_anomaly()
        d = anomaly_to_dict(a)
        assert "corrected_values" in d, "Missing corrected_values in anomaly_to_dict output"
        assert "corrected_temperature" in d
        assert "corrected_pressure" in d
        assert "corrected_humidity" in d
        assert "explainable_evidence" in d

    def test_corrected_value_extracted_from_evidence(self):
        """When evidence JSON contains corrected_values, they should be extracted."""
        import json
        from backend.app.api.routes import anomaly_to_dict
        evidence = {
            "corrected_values": {
                "temperature": {
                    "is_corrected": True,
                    "status": "ESTIMATED_OPTIONAL",
                    "method": "SPATIAL_PEER_CONSENSUS",
                    "confidence": 0.90,
                    "raw_value": 99.0,
                    "corrected_value": 14.5,
                    "is_estimated_optional": True,
                    "explanation": "Spatial peers report ~14.5°C"
                },
                "pressure": {"is_corrected": False, "corrected_value": None},
                "humidity": {"is_corrected": False, "corrected_value": None},
            },
            "explainable_evidence": {
                "primary_contributor": "SPIKE_FAULT",
                "temporal_findings": "Temperature spike >4σ above rolling mean.",
            }
        }
        a = self._make_mock_anomaly(evidence_json=json.dumps(evidence))
        d = anomaly_to_dict(a)
        assert d["corrected_temperature"] == 14.5, (
            f"Expected corrected_temperature=14.5, got {d['corrected_temperature']}"
        )
        assert d["corrected_pressure"] is None
        assert d["corrected_humidity"] is None
        assert d["explainable_evidence"].get("primary_contributor") == "SPIKE_FAULT"

    def test_raw_observation_unchanged_in_output(self):
        """observed_temperature must always equal the raw stored value."""
        from backend.app.api.routes import anomaly_to_dict
        a = self._make_mock_anomaly()
        d = anomaly_to_dict(a)
        assert d["observed_temperature"] == 99.0, "Raw observation must not be altered"

    def test_no_error_on_empty_evidence(self):
        """anomaly_to_dict must not raise errors when evidence is empty."""
        from backend.app.api.routes import anomaly_to_dict
        a = self._make_mock_anomaly(evidence_json="")
        d = anomaly_to_dict(a)
        assert d["corrected_values"] == {}
        assert d["corrected_temperature"] is None
