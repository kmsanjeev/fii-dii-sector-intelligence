---

# UPDATE V1.1

**Date:** 2026-06-01

## Purpose

The Institutional Positioning Engine measures institutional participation and positioning using NSE participant statistics.

The objective is to identify whether institutional participants are accumulating or distributing market exposure.

---

## Data Sources

### Participant Wise Open Interest

Source:

NSE Participant Open Interest Statistics

Captures:

* FII Positioning
* DII Positioning
* Proprietary Trader Positioning
* Client Positioning

---

### Participant Wise Trading Volume

Source:

NSE Participant Trading Volume Statistics

Captures:

* FII Activity
* DII Activity
* Proprietary Activity
* Client Activity

---

### FII Derivatives Statistics

Source:

NSE FII Derivatives Report

Captures:

* Futures Buy Contracts
* Futures Sell Contracts
* Net Futures Activity

---

## Calculated Metrics

Generated Metrics:

* FII_OI_Net

* DII_OI_Net

* PRO_OI_Net

* CLIENT_OI_Net

* FII_Volume_Net

* DII_Volume_Net

* PRO_Volume_Net

* CLIENT_Volume_Net

* FII_Derivatives_Net

---

## Institutional Score

The engine combines participant positioning and derivatives activity into a single Institutional Score.

Components:

* Open Interest Weighting
* Volume Weighting
* Derivatives Weighting

Output:

Institutional_Score

---

## Regime Classification

Generated Regimes:

### ACCUMULATION

Institutional participants are increasing market exposure.

### DISTRIBUTION

Institutional participants are reducing market exposure.

### NEUTRAL

No significant directional positioning.

---

## Generated Output

File:

data/intelligence/institutional_positioning.csv

---

## Historical Integration

The engine feeds:

data/historical/institutional/institutional_positioning_history.csv

Current Coverage:

2016-01-01 → 2026-05-29

Records:

2560+

---

## Current Status

Production Ready
