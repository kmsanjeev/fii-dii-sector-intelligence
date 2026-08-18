# POSITION_END Control-Design Registry

No control dates were generated in this activity. The frozen acquisition
offsets remain historical, unscored preparation and are not a valid day-level
risk set for YEAR records.

| Candidate | Estimand | Control selection | Time matching | Required data | Current status |
|---|---|---|---|---|---|
| Within-subject case-crossover | Exposure/feature state at a formal effective end versus eligible non-event windows for the same subject | Same subject, outside event and exclusion windows | Calendar date and season matched | Exact event day, complete role interval, repeated-event rules | PARTIAL / not executable |
| Risk-set matched controls | Conditional event-time comparison among subjects at risk at the same calendar time | Subjects with documented active role and no competing end event | Calendar time, age/tenure and role class | Population at risk, role starts, censoring and exact event dates | PREFERRED FUTURE DESIGN |
| Person-time sampled controls | Rate comparison over documented person-time at risk | Reproducible person-time sampling | Calendar and tenure bands | Complete start/end/censoring intervals and exposure history | DEFERRED |

The preferred future design is a risk-set design, with a within-subject
case-crossover alternative where a complete role interval and exchangeable
control windows can be defended. Seasonality, calendar time, age/tenure,
competing events and source dependence must be pre-specified. No final control
dates can be selected while all current role-start risk intervals are
unavailable.

Future multiplicity control must be declared before scoring: one primary
hypothesis/estimand, Holm family-wise control for the confirmatory family, and
maximum-statistic permutation only where exchangeability is justified. FDR is
exploratory only.
