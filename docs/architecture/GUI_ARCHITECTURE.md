# GUI ARCHITECTURE

## Project

FII/DII Capital Flow Intelligence Platform

---

# Purpose

This document defines the User Interface (UI), User Experience (UX), Dashboard Architecture, Visualization Framework, Infographic Framework, Navigation System, and User Interaction Model for the platform.

The objective is to transform complex market intelligence into a simple, intuitive, and visually engaging experience.

---

# GUI Vision

The platform should feel like:

Bloomberg Terminal
+
TradingView
+
AI Research Assistant
+
Portfolio Manager

while remaining understandable to a first-time investor.

---

# GUI Philosophy

## Principle 1

Answers Before Data

Users should receive answers first.

Data should support the answer.

---

## Principle 2

Visualization Before Tables

Prefer:

Maps

Heatmaps

Infographics

Timelines

Charts

before large tables.

---

## Principle 3

AI First

The primary interface should eventually be AI-driven.

Users should be able to ask:

"What sector is accumulating?"

instead of searching manually.

---

## Principle 4

Three-Second Rule

A user should understand the current market condition within three seconds of opening the dashboard.

---

## Principle 5

Progressive Disclosure

Show:

Overview

↓

Sector

↓

Theme

↓

Stock

↓

Details

Avoid overwhelming the user.

---

# User Types

## Type 1

Child Mode

Purpose:

Education

Backtesting

Market Learning

Simulation

---

Restrictions:

No Broker Access

No Live Trading

No Portfolio Execution

---

## Type 2

Investor Mode

Purpose:

Investment Research

Portfolio Tracking

Watchlists

---

## Type 3

Trader Mode

Purpose:

Swing Trading

Positional Trading

Opportunity Tracking

---

## Type 4

Professional Mode

Purpose:

Research

Portfolio Analysis

Advanced Intelligence

---

## Type 5

Administrator Mode

Purpose:

Platform Management

Research Management

Development Governance

---

# Navigation Architecture

## Level 1

Primary Navigation

```text
Dashboard

Market

Sectors

Themes

Stocks

Portfolio

Research

AI Assistant

Reports

Settings
```

---

# Home Dashboard

## Objective

Provide a complete market overview.

---

## Components

### Market Regime Card

Examples:

Accumulation

Distribution

Risk-On

Risk-Off

---

### Institutional Flow Card

FII

DII

PRO

CLIENT

---

### Capital Flow Map

Market

↓

Sector

↓

Theme

↓

Stock

---

### Top Opportunities

Top Accumulating Stocks

Top Sectors

Top Themes

---

### Watchlist Alerts

Generated Signals

Generated Opportunities

---

# Market Dashboard

## Objective

Understand overall market condition.

---

## Sections

Market Regime

Institutional Flow

Breadth

Volatility

Leadership

Risk Metrics

---

# Sector Dashboard

## Objective

Identify sector rotation.

---

## Components

Sector Heatmap

Sector Ranking

Sector Momentum

Sector Capital Flow

Sector Conviction

Sector Leadership

---

# Theme Dashboard

## Objective

Identify theme rotation.

---

## Components

Theme Heatmap

Theme Ranking

Theme Momentum

Theme Capital Flow

Theme Leadership

---

# Stock Dashboard

## Objective

Analyze a single stock.

---

## Components

Price Action

Volume Analysis

Delivery Analysis

Accumulation Score

Institutional Score

Fundamental Score

Risk Score

---

## AI Summary

Examples:

Why is the stock moving?

What changed?

What should be monitored?

---

# Portfolio Dashboard

## Objective

Portfolio intelligence.

---

## Components

Allocation

Sector Exposure

Theme Exposure

Risk Score

Opportunity Score

Portfolio Health

---

## AI Portfolio Review

Examples:

Portfolio Strength

Portfolio Weakness

Concentration Risk

Suggestions

---

# Research Dashboard

## Objective

Manage research lifecycle.

---

## Components

Research Backlog

Validation Queue

Approved Research

Archived Research

---

# AI Dashboard

## Objective

Primary interaction layer.

---

## Components

AI Chat

AI Analyst

AI Research Assistant

AI Portfolio Manager

AI Development CTO

---

## Example Questions

Which sectors are accumulating?

Why is IT outperforming?

Which themes are emerging?

Show stocks with strong institutional accumulation.

---

# Reporting Center

## Objective

Centralized report access.

---

## Categories

Daily Reports

Weekly Reports

Monthly Reports

Research Reports

Portfolio Reports

---

# Visualization Framework

## Preferred Visualizations

### Tier 1

Highest Priority

Heatmaps

Treemaps

Capital Flow Maps

Trend Maps

Infographics

---

### Tier 2

Medium Priority

Bar Charts

Line Charts

Rankings

Scorecards

---

### Tier 3

Lowest Priority

Large Tables

Raw Data Grids

---

# Infographic Framework

## Objective

Increase understanding and engagement.

---

## Types

Market Infographics

Sector Infographics

Theme Infographics

Stock Infographics

Portfolio Infographics

Research Infographics

---

## Principles

Simple

Visual

Actionable

Memorable

---

# Capital Flow Visualization

## Flow Model

```text
Market
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

---

## Visual Format

Interactive Flow Maps

Color-Coded Momentum

Directional Arrows

Strength Indicators

---

# Notification Framework

## Categories

Market Alerts

Sector Alerts

Theme Alerts

Stock Alerts

Portfolio Alerts

Research Alerts

---

# Mobile Architecture

## Objective

Mobile-first consumption.

---

## Focus Areas

Watchlists

Alerts

Reports

AI Assistant

Portfolio Monitoring

---

## Heavy Analytics

Remain on desktop.

---

# Accessibility

## Requirements

Simple Language

Visual Indicators

Color + Text Indicators

Mobile Compatibility

Keyboard Navigation

---

# Dashboard Performance

## Rules

Load summaries first.

Load details on demand.

Avoid full-universe processing during interaction.

Use cache whenever possible.

---

# Future Enhancements

Voice Assistant

AI Copilot

Interactive Research Maps

Broker Trading Panel

Strategy Builder

Portfolio Simulator

---

# Long-Term Vision

Create the most user-friendly Capital Flow Intelligence Platform capable of allowing any user to answer:

What is happening?

Why is it happening?

What should I watch?

What should I do next?

within seconds, using a combination of AI, visualization, and market intelligence.

The platform should feel less like software and more like a personal market operating system.
