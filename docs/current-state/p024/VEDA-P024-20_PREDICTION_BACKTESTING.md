# Prediction and Backtesting

{
  "contract_id": "VEDA-P024-PREDICTION-CONTRACT",
  "domain": "MARRIAGE",
  "supported_prediction_types": [
    "EXPERIMENTAL_PREDICTION",
    "SHADOW_PREDICTION"
  ],
  "supported_prediction_states": [
    "RESEARCH_ONLY",
    "EXPERIMENTAL",
    "SHADOW"
  ],
  "supported_fields": [
    "prediction_id",
    "domain",
    "created_at",
    "window_start",
    "window_end",
    "prediction_type",
    "prediction_state",
    "supporting_evidence",
    "opposing_evidence",
    "cancelling_evidence",
    "method_version",
    "rule_versions",
    "confidence_state",
    "actual_outcome",
    "outcome_recorded_at",
    "comparison_result"
  ],
  "comparison_policy": "recorded_outcome_compares_against_prediction_state",
  "future_uses": [
    "backtesting",
    "calibration",
    "accuracy_statistics",
    "ml_feature_generation",
    "rule_refinement"
  ],
  "production_activation": "NOT_REQUIRED"
}
