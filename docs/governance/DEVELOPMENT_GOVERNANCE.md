# DEVELOPMENT GOVERNANCE

## Project

FII/DII Capital Flow Intelligence Platform

---

# Purpose

This document defines the development standards, governance framework, architectural rules, documentation requirements, testing procedures, and release management process for the platform.

All future development must comply with this governance framework.

---

# Development Philosophy

The platform shall be developed using:

Data First
→ Intelligence Second
→ AI Third
→ Presentation Fourth
→ Execution Fifth

No module shall be developed without a clear architectural purpose.

---

# Core Principles

## Principle 1

Raw Data Never Modified

Source data remains immutable.

Examples:

* NSE Bhavcopy
* F&O Bhavcopy
* Institutional Data
* Corporate Actions
* Equity Master

Raw datasets are considered the permanent source of truth.

---

## Principle 2

Derived Data Must Be Rebuildable

All derived outputs must be capable of being regenerated from source data.

Examples:

* Intelligence Files
* Signals
* Reports
* Infographics
* AI Knowledge Artifacts

---

## Principle 3

Cache Is Disposable

Cache exists solely for performance optimization.

Cache must never become the source of truth.

Cache may be deleted and rebuilt at any time.

---

## Principle 4

Documentation Before Complexity

Major architectural decisions must be documented before implementation.

---

## Principle 5

User Experience Before Technical Elegance

The platform exists to create clarity.

Complexity should remain hidden behind intuitive interfaces.

---

# Development Workflow

## Stage 1

Research

Activities:

* Idea Discovery
* Data Discovery
* Market Research
* Feasibility Assessment

Output:

Research Proposal

---

## Stage 2

Architecture

Activities:

* Solution Design
* Data Design
* Dependency Analysis

Output:

Architecture Approval

---

## Stage 3

Development

Activities:

* Code Creation
* Integration
* Refactoring

Output:

Working Module

---

## Stage 4

Validation

Activities:

* Data Validation
* Functional Testing
* Integrity Testing

Output:

Validated Module

---

## Stage 5

Documentation

Activities:

* Update Architecture
* Update Checklists
* Update Changelog

Output:

Updated Documentation

---

## Stage 6

Release

Activities:

* Merge
* Version Tag
* Deployment

Output:

Production Release

---

# Coding Standards

## Rule 1

Complete file replacements preferred over partial code snippets.

---

## Rule 2

All delivered code must be copy-paste ready.

---

## Rule 3

Git commit commands must accompany code changes.

---

## Rule 4

Avoid unnecessary dependencies.

---

## Rule 5

Maintain backward compatibility whenever possible.

---

# Data Governance

## Data Hierarchy

Level 1

Raw Data

Examples:

* NSE Data
* Institutional Data

---

Level 2

Cache

Examples:

* Stock History Cache
* Sector Cache

---

Level 3

Intelligence

Examples:

* Capital Flow
* Sector Rotation
* Theme Rotation

---

Level 4

Signals

Examples:

* Watchlists
* Trade Candidates

---

Level 5

Reports

Examples:

* Daily Reports
* Weekly Reports
* Monthly Reports

---

# NSE Data Policy

## Official Policy

Preferred data acquisition order:

1. nselib
2. NSE API
3. Alternative Sources
4. yFinance

Use fallback only when higher-priority sources fail.

---

# Cache Governance

## Cache Philosophy

Cache exists to reduce processing time.

Cache must:

* Be rebuildable
* Be version independent
* Be automatically refreshable

---

## Stock Cache Policy

Stock cache shall be generated on demand.

Workflow:

User Request
→ Check Cache
→ Build Cache if Missing
→ Return Result

---

## Cache Maintenance Policy

Heavy cache updates shall occur:

* After Market Hours
* Overnight
* Weekends

Avoid intensive processing during market hours.

---

# Architecture Decision Records (ADR)

## Purpose

Record major architectural decisions.

---

## Location

docs/decisions/

---

## Examples

ADR-001

Raw Data Never Modified

---

ADR-002

NSE Data Folder Structure

---

ADR-003

On Demand Cache Architecture

---

ADR-004

Listing Date Aware Processing

---

ADR-005

nselib First Policy

---

# Documentation Governance

## Mandatory Documents

* PROJECT_SCOPE.md
* MASTER_ROADMAP.md
* MODULE_REGISTRY.md
* MASTER_CHECKLIST.md

---

## Architecture Documents

Must be updated whenever architecture changes.

---

## Module Documents

Must be updated whenever module scope changes.

---

# Research Governance

All new ideas must follow:

Idea
→ Research
→ Validation
→ Approval
→ Development

No direct implementation without validation.

---

# Testing Governance

## Required Validation Types

### Data Validation

Verify correctness of data.

---

### Integrity Validation

Verify completeness of datasets.

---

### Functional Validation

Verify expected behavior.

---

### Regression Validation

Verify older functionality remains intact.

---

# Release Governance

## Versioning

Major.Minor.Patch

Examples:

1.0.0

1.1.0

1.1.1

---

## Release Requirements

Before release:

* Code Complete
* Validation Complete
* Documentation Updated
* Checklist Updated

---

# Dashboard Governance

Development Dashboard must track:

* Phase Progress
* Module Progress
* Active Tasks
* Blocked Tasks
* Research Backlog
* Technical Debt

---

# Long-Term Objective

Create a scalable, maintainable, AI-powered Capital Flow Intelligence Platform capable of supporting:

Market Intelligence

Sector Intelligence

Theme Intelligence

Stock Intelligence

Fundamental Intelligence

Artificial Intelligence

Portfolio Intelligence

Execution Intelligence

within a unified governance framework.
