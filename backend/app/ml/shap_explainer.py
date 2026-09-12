"""
SkyGuard AI - Feature Attribution Module (Compatibility Wrapper)
Redirects to SkyGuardFeatureAttributor to ensure honest terminology without misleading SHAP claims.
"""
from .feature_attribution import SkyGuardFeatureAttributor as SkyGuardShapExplainer, SkyGuardFeatureAttributor

__all__ = ["SkyGuardFeatureAttributor", "SkyGuardShapExplainer"]
