# ADR-006

## Title

Gross Flow Preservation

---

# Status

Accepted

---

# Date

2026-06-03

---

# Decision Type

Data Architecture

Institutional Intelligence

---

# Context

The current Institutional Intelligence implementation primarily stores net positioning metrics.

Examples:

FII_OI_Net

DII_OI_Net

PRO_OI_Net

CLIENT_OI_Net

FII_Derivatives_Net

Institutional_Score

---

While net figures are useful for regime classification, they do not preserve complete market behavior.

Important information is lost when:

Buying

Selling

Position Building

Position Unwinding

are reduced into a single net value.

---

# Problem Statement

Net figures cannot fully explain:

Who is buying?

Who is selling?

How much conviction exists?

Whether both sides are active?

Whether positions are being built or closed?

---

## Example

Scenario A

Buy:

₹10,000 Cr

Sell:

₹9,000 Cr

Net:

+₹1,000 Cr

---

Scenario B

Buy:

₹1,200 Cr

Sell:

₹200 Cr

Net:

+₹1,000 Cr

---

Both produce:

Net:

+₹1,000 Cr

---

However:

Market behavior is completely different.

Conviction is different.

Liquidity is different.

Participation is different.

---

# Decision

Future versions of Institutional Intelligence shall preserve:

Gross Buying

Gross Selling

Net Flow

independently.

---

# Required Data Model

Instead of:

```text id="w91y8g"
FII_Net
```

the platform should store:

```text id="frgt0i"
FII_Buy

FII_Sell

FII_Net
```

---

Likewise:

```text id="vgt72d"
DII_Buy

DII_Sell

DII_Net
```

---

```text id="ol6ax7"
PRO_Buy

PRO_Sell

PRO_Net
```

---

```text id="n35mwm"
CLIENT_Buy

CLIENT_Sell

CLIENT_Net
```

---

# Institutional Data Philosophy

Institutional datasets should preserve:

Activity

Positioning

Flow

separately.

---

## Activity

Who traded?

How much traded?

---

## Positioning

Who is long?

Who is short?

---

## Flow

Where is capital moving?

---

# Benefits

---

## Benefit 1

Preserves Raw Information

No information loss.

---

## Benefit 2

Improves Conviction Analysis

Allows distinction between:

High Conviction

Low Conviction

Neutral Activity

---

## Benefit 3

Improves AI Analysis

AI can explain:

Buying Pressure

Selling Pressure

Participation

Capital Rotation

---

## Benefit 4

Improves Capital Flow Intelligence

Provides stronger signals for:

Sector Rotation

Theme Rotation

Stock Accumulation

---

## Benefit 5

Supports Future Smart Money Models

Allows development of:

Participation Scores

Conviction Scores

Liquidity Scores

Flow Scores

---

# Impacted Modules

Institutional Intelligence

Sector Intelligence

Theme Intelligence

Stock Intelligence

Portfolio Intelligence

AI Platform

Reporting Platform

---

# Implementation Strategy

Version 1

Existing Net-Based System

Remain Operational

---

Version 2

Add Gross Buy

Add Gross Sell

Preserve Net

---

Version 3

Introduce:

Flow Intelligence Layer

Conviction Layer

Participation Layer

---

# Migration Policy

Existing datasets shall not be deleted.

New fields should be added through backward-compatible updates.

---

# Relationship To Project Vision

The project objective is:

Follow the Money

---

Money movement is better represented by:

Gross Buying

Gross Selling

Positioning

than by net values alone.

---

# Long-Term Outcome

The platform shall evolve from:

Net Position Intelligence

to

Full Capital Flow Intelligence

while preserving historical compatibility and improving analytical depth.
