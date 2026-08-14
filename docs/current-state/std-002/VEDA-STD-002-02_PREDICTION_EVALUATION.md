# Prediction and Evaluation

Predictions are created before outcomes, with a deterministic ID from request/subject/domain/description/window. Outcome capture is separate and immutable after recording. Event and direction comparison are implemented; timing-error and confidence calibration require sufficient timestamped outcome data and report `INSUFFICIENT_SAMPLE` otherwise.
