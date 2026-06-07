# ADR-020 – Corporate Intelligence Layer

Status: Approved

Date: 2026-06-06

## Objective

Transform the platform from a Market Intelligence Platform into a complete:

* Market Intelligence Platform
* Fundamental Intelligence Platform
* Institutional Intelligence Platform
* Management Intelligence Platform
* Governance Intelligence Platform

capable of identifying emerging leaders, institutional accumulation, management confidence shifts, earnings acceleration and future bull-run candidates.

---

## Strategic Goal

Identify:

* Emerging Leaders
* Bull Run Candidates
* Institutional Accumulation
* Management Confidence
* Fundamental Strength
* Governance Risks

before they become obvious to the broader market.

---

## Architecture Overview

Market Intelligence Layer
→ Corporate Intelligence Layer
→ Management Intelligence Layer
→ Governance Intelligence Layer
→ Bull Run Intelligence Layer

---

## Domain 1 – Market Intelligence

Status: Implemented

Includes:

* Bhavcopy Import Engine
* Equity Master Engine
* Classification Engine
* Index Intelligence Engine
* Index Taxonomy Engine
* Historical Snapshot Engine
* Leadership Persistence Engine

Outputs:

* Price Strength
* Volume Trends
* Momentum
* Sector Rotation
* Theme Rotation
* Leadership Signals

---

## Domain 2 – Fundamental Intelligence

Source:

NSE Financial Results

Future Engine:

financial_results_engine.py

Store:

* Revenue
* EBITDA
* PAT
* EPS
* Margins
* ROE
* ROCE

Outputs:

* fundamental_growth.csv
* earnings_acceleration.csv
* margin_trends.csv

Purpose:

Detect earnings acceleration and improving business performance.

---

## Domain 3 – Ownership Intelligence

Source:

NSE Shareholding Pattern

Future Engine:

shareholding_engine.py

Store:

* Promoter Holding
* FII Holding
* DII Holding
* Public Holding
* Others

Outputs:

* ownership_trends.csv
* institutional_accumulation.csv

Purpose:

Track institutional accumulation and ownership changes.

---

## Domain 4 – Corporate Event Intelligence

Includes:

* Announcements
* Board Meetings
* Corporate Actions

Future Engines:

* announcement_engine.py
* board_meeting_engine.py
* corporate_actions_engine.py

Track:

* Order Wins
* Contracts
* Capacity Expansion
* Bonus
* Split
* Dividend
* Fund Raising
* Acquisitions

Purpose:

Identify growth catalysts and event-driven opportunities.

---

## Domain 5 – Management Intelligence

Includes:

* Conference Calls
* Call Recordings
* Transcripts
* Management Commentary
* Guidance

### Conference Call Engine

Future Engine:

conference_call_engine.py

Capture:

* Audio
* PDF
* Transcripts

### Transcript Engine

Future Engine:

transcript_engine.py

Convert:

* Audio
* PDF

into structured text.

### Commentary Intelligence Engine

Future Engine:

management_intelligence_engine.py

Extract:

* Order Book Commentary
* Pipeline Commentary
* Capacity Expansion Commentary
* Demand Outlook
* Export Outlook
* Margin Outlook
* Guidance
* Capex Plans

Outputs:

* management_signals.csv

### Management Sentiment Engine

Generate:

Management Confidence Score

Categories:

* Very Positive
* Positive
* Neutral
* Negative
* Very Negative

Outputs:

* management_sentiment.csv

Purpose:

Detect early signals of future business acceleration before they appear in reported financials.

---

## Domain 6 – Governance Intelligence

Future Engine:

governance_engine.py

Track:

* Auditor Changes
* Promoter Pledge
* Related Party Transactions
* Senior Management Resignations
* Governance Concerns

Outputs:

* governance_risk.csv

Purpose:

Identify hidden risks and governance deterioration.

---

## Bull Run Intelligence Layer

Future Engine:

bull_run_probability_engine.py

Inputs:

* Price Momentum
* Sector Leadership
* Theme Leadership
* Revenue Growth
* PAT Growth
* FII Accumulation
* DII Accumulation
* Management Confidence
* Order Book Expansion
* Governance Risk

Outputs:

* bull_run_probability.csv

Purpose:

Estimate the probability that a stock is entering or sustaining a bull run.

---

## Multi-Factor Ranking Layer

Future Engine:

stock_ranking_engine.py

Evaluate:

* Technical Strength
* Fundamental Strength
* Ownership Strength
* Management Strength
* Governance Strength

Outputs:

* stock_rankings.csv

Purpose:

Generate platform-wide stock rankings.

---

## Storage Architecture

data/
└── NSE/
├── bhavcopy/
├── equity_master/
├── indices/
└── corporate/
├── announcements/
├── board_meetings/
├── corporate_actions/
├── financial_results/
├── shareholding/
├── governance/
├── call_recordings/
└── transcripts/

---

## Backup Policy

Inherited from ADR-019.

Weekly Incremental Backup:

Friday 23:59 IST

Mandatory secondary backup.

---

## Integrity Policy

Inherited from ADR-019.

Every engine must support:

* Missing File Detection
* Corruption Detection
* Schema Validation
* Automatic Recovery
* Backup Recovery
* Re-download Capability

---

## Frozen Development Sequence

1. Leadership Persistence Engine V1.1 Integration
2. Auto Classification Engine V2 Integration
3. Financial Results Engine
4. Shareholding Intelligence Engine
5. Announcement Intelligence Engine
6. Conference Call Engine
7. Transcript Engine
8. Management Intelligence Engine
9. Governance Engine
10. Bull Run Probability Engine
11. Stock Ranking Engine

---

## Approved Outcome

The platform evolves into a complete:

* Market Intelligence System
* Fundamental Intelligence System
* Institutional Intelligence System
* Management Intelligence System
* Governance Intelligence System

capable of identifying emerging market leaders significantly earlier than traditional price-only approaches.
