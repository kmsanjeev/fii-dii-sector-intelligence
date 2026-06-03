# ADR-016

## Title

Participant Intelligence Framework

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

The project originally focused on Institutional Intelligence using FII and DII participant data.

As the platform evolved, it became evident that limiting analysis to institutional participants would leave valuable information unutilized.

Market behavior is influenced by multiple participant categories:

* FII
* DII
* PRO
* CLIENT

Each participant group contributes unique information regarding capital flow, conviction, sentiment, and positioning.

To support the long-term vision of identifying capital movement before broad market recognition, a broader participant-centric architecture is required.

---

# Decision

The platform shall adopt a Participant Intelligence Framework.

Future intelligence systems shall analyze:

FII

DII

PRO

CLIENT

as separate participant groups.

---

# Participant Definitions

---

## FII

Foreign Institutional Investors

Represents:

Global capital allocation.

---

## DII

Domestic Institutional Investors

Represents:

Domestic capital allocation.

---

## PRO

Professional / Proprietary Participants

Represents:

Professional trading activity.

---

## CLIENT

Retail and Non-Institutional Participants

Represents:

Retail participation and sentiment.

---

# Architecture Impact

The architecture hierarchy becomes:

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
    ↓
Fundamental Validation
    ↓
Portfolio
    ↓
Execution
```

Participant Intelligence becomes the foundational intelligence layer.

---

# New Intelligence Capabilities

The framework enables:

Participant Flow Analysis

Participant Conviction Analysis

Participant Divergence Analysis

Smart Money Analysis

Retail Sentiment Analysis

Consensus Detection

Conflict Detection

---

# Benefits

---

## Benefit 1

Improved Capital Flow Visibility

Track all major participant groups rather than only institutions.

---

## Benefit 2

Smart Money Detection

Identify accumulation by informed participants.

---

## Benefit 3

Retail Sentiment Detection

Identify crowd participation and potential excesses.

---

## Benefit 4

Divergence Analysis

Detect disagreements between participant categories.

---

## Benefit 5

Earlier Opportunity Detection

Improve identification of:

Sector Rotation

Theme Rotation

Stock Leadership

before broad market recognition.

---

# Consequences

Positive:

More comprehensive capital flow analysis.

Better opportunity discovery.

Improved participant visibility.

Improved AI analysis.

Improved research quality.

---

Negative:

Additional data processing requirements.

Additional intelligence layer complexity.

More datasets and dashboards to maintain.

---

# Implementation Plan

Phase 1

Participant Intelligence Documentation

---

Phase 2

Participant Flow Engine

Participant Conviction Engine

---

Phase 3

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

Phase 4

Participant Dashboard

Participant Reports

Participant Infographics

AI Participant Analyst

---

# Related ADR

ADR-006 Gross Flow Preservation

ADR-007 Sector Theme Stock Capital Flow Model

ADR-009 Intelligence Layer Separation

ADR-010 AI First User Experience

---

# Final Decision

The Capital Flow Intelligence Platform shall evolve from:

```text
Institutional Intelligence
```

to:

```text
Participant Intelligence
```

by treating:

FII

DII

PRO

CLIENT

as equal analytical participants within the capital flow framework.

This decision becomes a foundational architectural principle for all future platform development.
