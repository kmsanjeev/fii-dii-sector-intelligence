# Power and Sample Standard

Required preregistration fields: baseline prevalence, minimum detectable effect
(absolute and relative), alpha, target power, allocation ratio, design effect,
matching/control efficiency, clustering, multiplicity correction, date
precision, missingness/exclusions, and primary estimand.

`scripts/veda_power_planner.py` provides reproducible sensitivity tables for
baseline rates 10%, 20%, and 30% with 5/10/15/20 percentage-point effects.
Holm and maximum-statistic permutation are confirmatory-safe options; FDR is
exploratory only. Exact conditional/permutation planning must follow once a
real event family and risk sets are frozen.
