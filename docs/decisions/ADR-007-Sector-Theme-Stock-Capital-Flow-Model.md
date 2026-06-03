# ADR-007

## Title

Sector → Theme → Stock Capital Flow Model

---

# Status

Accepted

---

# Date

2026-06-03

---

# Decision Type

Core Platform Architecture

Capital Flow Intelligence

---

# Context

The primary objective of the platform is:

Follow the Money.

The challenge is that institutional capital rarely appears directly at the stock level first.

Capital typically flows through multiple layers before becoming visible.

Traditional market analysis focuses on:

Stock
→ Price
→ News

This often identifies opportunities late.

The platform requires a framework capable of identifying capital movement before broad market recognition.

---

# Decision

The platform shall adopt the following Capital Flow Hierarchy:

```text
Market
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

All future intelligence modules shall align with this hierarchy.

---

# Capital Flow Theory

Institutional capital generally enters markets in stages.

---

## Stage 1

Market Allocation

Examples:

Risk-On

Risk-Off

Domestic Allocation

Global Allocation

---

## Stage 2

Sector Allocation

Examples:

IT

Banking

Capital Goods

Defence

Power

Healthcare

---

## Stage 3

Theme Allocation

Examples:

Data Centres

Defence Electronics

AI Infrastructure

Renewable Energy

Railways

Manufacturing

---

## Stage 4

Stock Allocation

Examples:

KPIT

BEL

HAL

ABB

LTTS

---

# Why This Matters

Stock movement is often a consequence.

Sector and theme movement are often the cause.

The platform seeks to identify the cause before the consequence becomes obvious.

---

# Intelligence Hierarchy

---

## Layer 1

Market Intelligence

Purpose:

Detect overall market conditions.

Examples:

Accumulation

Distribution

Risk-On

Risk-Off

---

## Layer 2

Sector Intelligence

Purpose:

Identify where large pools of capital are moving.

Examples:

IT Accumulation

Defence Rotation

Power Leadership

---

## Layer 3

Theme Intelligence

Purpose:

Identify emerging narratives.

Examples:

Data Centres

Defence Electronics

Transmission Infrastructure

Industrial Automation

---

## Layer 4

Stock Intelligence

Purpose:

Identify the specific beneficiaries of capital flow.

Examples:

Early Accumulation

Strong Accumulation

Leadership Stocks

Breakout Candidates

---

# Capital Flow Detection Model

The platform shall evaluate:

---

## Institutional Activity

FII

DII

PRO

CLIENT

---

## Price Behavior

Relative Strength

Momentum

Trend

---

## Volume Behavior

Volume Expansion

Volume Contraction

Participation

---

## Delivery Behavior

Delivery Percentage

Delivery Expansion

---

## F&O Behavior

Open Interest

Position Building

Long Build-Up

Short Covering

---

## Fundamental Confirmation

Results

Order Books

Concall Commentary

Shareholding Changes

Corporate Actions

---

# Sector Intelligence Responsibilities

Sector Intelligence shall answer:

Which sectors are attracting capital?

Which sectors are losing capital?

Which sectors are accelerating?

Which sectors are weakening?

---

# Theme Intelligence Responsibilities

Theme Intelligence shall answer:

Which themes are emerging?

Which themes are strengthening?

Which themes are weakening?

Which themes are becoming crowded?

---

# Stock Intelligence Responsibilities

Stock Intelligence shall answer:

Which stocks are attracting capital?

Which stocks are leading their theme?

Which stocks are leading their sector?

Which stocks show accumulation characteristics?

---

# Opportunity Discovery Framework

The preferred sequence shall be:

```text
Market
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

Not:

```text
Stock
    ↓
Sector
    ↓
Theme
```

---

# Example

Scenario:

Institutional Accumulation Detected

↓

IT Sector Strengthening

↓

Digital Engineering Theme Strengthening

↓

KPIT Strengthening

↓

Opportunity Identified

---

# Conviction Framework

The highest conviction opportunities occur when:

Market Alignment

*

Sector Alignment

*

Theme Alignment

*

Stock Alignment

exist simultaneously.

---

## Example

Market:

Accumulation

---

Sector:

IT Leadership

---

Theme:

Digital Engineering

---

Stock:

KPIT Strong Accumulation

---

Result:

High Conviction Opportunity

---

# AI Responsibilities

Future AI agents must follow this hierarchy.

---

## AI Market Analyst

Market Layer

---

## AI Sector Analyst

Sector Layer

---

## AI Theme Analyst

Theme Layer

---

## AI Stock Analyst

Stock Layer

---

# Dashboard Responsibilities

The GUI shall visualize:

```text
Market
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

through:

Capital Flow Maps

Heatmaps

Rotation Maps

Opportunity Maps

---

# Reporting Responsibilities

Reports shall prioritize:

1. Market
2. Sector
3. Theme
4. Stock

in that order.

---

# Relationship To Project Vision

This ADR becomes the central intelligence model of the platform.

All future modules must support the ability to answer:

Where is money flowing?

Why is money flowing there?

Which stocks benefit?

How early was the opportunity identified?

---

# Impacted Modules

Institutional Intelligence

Sector Intelligence

Theme Intelligence

Stock Intelligence

Fundamental Intelligence

AI Platform

Portfolio Intelligence

Reporting Platform

Dashboard Platform

Broker Platform

---

# Long-Term Outcome

The platform evolves from:

Data Collection

to

Capital Flow Intelligence

and ultimately becomes capable of identifying:

Market
→ Sector
→ Theme
→ Stock

opportunities before broad market recognition.

This ADR is considered a foundational architectural principle of the platform and shall guide future development decisions.
