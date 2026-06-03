# PARTICIPANT INTELLIGENCE

## Project

Capital Flow Intelligence Platform

---

# Module Overview

Participant Intelligence is the foundational intelligence layer of the platform.

Its purpose is to analyze the behavior of all major market participants and identify how capital enters, exits, and rotates throughout the market.

This module sits above raw market data and below all other intelligence layers.

---

# Capital Flow Framework

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

Participant Intelligence serves as the starting point of the entire Capital Flow framework.

---

# Objective

Answer the following questions:

1. Who is buying?
2. Who is selling?
3. Who has conviction?
4. Who is changing positioning?
5. Who is leading the market?
6. Who is following the market?
7. Where is smart money flowing?
8. Where is retail participation increasing?

---

# Participants Covered

---

## FII

Foreign Institutional Investors

Purpose:

Track global capital allocation.

---

## DII

Domestic Institutional Investors

Purpose:

Track domestic capital allocation.

---

## PRO

Professional / Proprietary Participants

Purpose:

Track professional trading activity and tactical positioning.

---

## CLIENT

Retail and Non-Institutional Participants

Purpose:

Track crowd behavior and sentiment.

---

# Why Participant Intelligence Matters

Markets are driven by participants.

Price movement is often the result of participant behavior.

Understanding participant behavior allows the platform to detect:

Capital Flow

↓

Sector Rotation

↓

Theme Rotation

↓

Stock Leadership

before broad market recognition.

---

# Data Sources

---

## NSE Participant Data

Provides:

FII Activity

DII Activity

PRO Activity

CLIENT Activity

---

## F&O Participant Statistics

Provides:

Long Positions

Short Positions

Open Interest

Volume Activity

---

## Cash Market Activity

Provides:

Participant Participation

Capital Flow

Volume Analysis

---

# Core Datasets

---

## Dataset 01

Participant History

Location

```text
data/intelligence/participant_history.csv
```

---

## Dataset 02

Participant Intelligence

Location

```text
data/intelligence/participant_intelligence.csv
```

---

## Dataset 03

Participant Divergence

Location

```text
data/intelligence/participant_divergence.csv
```

---

# Engines

---

## Engine 01

Participant Flow Engine

---

### Purpose

Measure capital movement by participant category.

---

### Outputs

Flow Score

Flow Direction

Flow Strength

---

### Status

Planned

---

## Engine 02

Participant Conviction Engine

---

### Purpose

Measure participant conviction.

---

### Inputs

Volume

Open Interest

Position Changes

Flow Changes

---

### Outputs

Conviction Score

Confidence Score

Participation Score

---

### Status

Planned

---

## Engine 03

Participant Divergence Engine

---

### Purpose

Measure disagreement between participant groups.

---

### Examples

FII vs CLIENT

PRO vs CLIENT

FII vs DII

Institutional vs Retail

---

### Outputs

Divergence Score

Conflict Score

Consensus Score

---

### Status

Planned

---

## Engine 04

Smart Money Engine

---

### Purpose

Identify informed capital.

---

### Inputs

FII

DII

PRO

---

### Outputs

Smart Money Score

Accumulation Score

Distribution Score

---

### Status

Planned

---

## Engine 05

Retail Sentiment Engine

---

### Purpose

Measure retail participation.

---

### Inputs

CLIENT Data

---

### Outputs

Retail Sentiment Score

Retail Conviction Score

Crowding Score

---

### Status

Planned

---

# Opportunity Framework

Highest conviction opportunities occur when:

```text
Smart Money Accumulation
+
Positive Sector Rotation
+
Positive Theme Rotation
+
Stock Leadership
```

---

# Outputs

Participant Scores

Flow Scores

Conviction Scores

Divergence Scores

Smart Money Scores

Retail Sentiment Scores

---

# Dashboard Integration

---

## Participant Dashboard

Components

Participant Flows

Conviction

Divergence

Smart Money

Retail Sentiment

Historical Trends

---

# AI Integration

---

## AI Participant Analyst

Questions Answered

Who is buying?

Who is selling?

Where is conviction increasing?

Where is smart money flowing?

Is retail chasing momentum?

---

# Relationship To Sector Intelligence

Participant Intelligence answers:

Who is moving capital?

---

Sector Intelligence answers:

Where is capital moving?

---

# Success Criteria

The module successfully identifies:

Participant Leadership

Participant Conviction

Participant Divergence

Smart Money Activity

Retail Behavior

before capital movement becomes obvious in sectors and stocks.

---

# Current Completion

0%

---

# Next Milestones

1. Participant Flow Engine

2. Participant Conviction Engine

3. Participant Divergence Engine

4. Smart Money Engine

5. Retail Sentiment Engine

6. Participant Dashboard

7. AI Participant Analyst

---

# Long-Term Vision

Create a participant-level intelligence system capable of identifying:

Who is moving capital,

Who is leading market behavior,

and where future opportunities are most likely to emerge.

Participant Intelligence becomes the foundation of the Capital Flow Intelligence Platform.
