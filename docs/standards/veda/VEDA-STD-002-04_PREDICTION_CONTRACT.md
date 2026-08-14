# Prediction Contract

`PredictionRecord` captures request, subject, domain, creation timestamp, testable event/window/direction, deterministic/classical/expert/empirical/ML evidence, opposing and cancelling evidence, uncertainties, rule/knowledge/model/workflow versions, and confidence. States include `HYPOTHESIS`, `EXPERIMENTAL_PREDICTION`, `SHADOW_PREDICTION`, `VALIDATION_ACTIVE`, `VALIDATED_PREDICTION`, `PRODUCTION_RESTRICTED`, and `PRODUCTION_ELIGIBLE`.

Prediction-time evidence is snapshotted. Outcomes are recorded separately and cannot rewrite a locked prediction.
