# Performance, Breadth and Leadership

Performance is an equal-weight proxy over usable current members for 1D, 3D,
5D, 10D and 20D windows. The benchmark is the existing provider benchmark
(`NIFTY 50 equal-weight constituent return proxy`). Relative strength is theme
proxy return minus benchmark return; it is not Sector relative strength.

Breadth reports expected members, usable members, coverage and positive
members. Unavailable stock prices are excluded, never coerced to zero.

Leadership states are deterministic `LEADING`, `IMPROVING`, `MIXED`,
`WEAKENING`, `LAGGING` or `INSUFFICIENT_HISTORY`. Persistence is explicitly
`INSUFFICIENT_HISTORY` until governed multi-date Theme history is available.
Acceleration is reported separately and is not described as capital rotation.
