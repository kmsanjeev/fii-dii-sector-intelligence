# ADR-019 – Data Integrity, Recovery & Backup Framework

Status: Approved

Date: 2026-06-06

## Objective

Ensure that all critical platform datasets remain complete, accurate, recoverable, auditable and self-healing.

The platform must never depend upon the user manually detecting missing or corrupted data.

---

## Problem Statement

The FII-DII Sector Intelligence Platform relies upon multiple critical datasets including:

* Bhavcopy Data
* Equity Master Data
* Index Intelligence Data
* Classification Data
* Corporate Intelligence Data
* Reference Data
* Derived Intelligence Data

Corrupted, missing, incomplete or stale datasets can produce incorrect intelligence outputs and lead to inaccurate portfolio decisions.

A permanent framework is required for:

* Integrity Validation
* Recovery
* Backup
* Auditability

---

## Decision

The platform shall implement a centralized:

* Data Integrity Framework
* Backup Framework
* Recovery Framework

covering all critical datasets.

---

## Data Integrity Policy

Every engine shall verify:

* File Exists
* File Readable
* Schema Valid
* Record Count Valid
* Required Columns Present

before using any dataset.

### Missing File Detection

The platform shall automatically detect:

* Deleted Files
* Missing Files
* Unexpected Absence

### Corrupt File Detection

The platform shall automatically detect:

* Unreadable CSV Files
* Malformed Files
* Invalid Formats
* Truncated Files

### Schema Validation

The platform shall verify:

* Expected Columns
* Column Names
* Data Types

### Record Count Validation

The platform shall verify:

* Minimum Expected Rows
* Historical Consistency

Example:

Equity Master should contain approximately 2,300+ NSE symbols.

If only 50 symbols are detected, the file shall be rejected automatically.

---

## Recovery Framework

Recovery hierarchy:

Primary Dataset
→ Secondary Backup
→ Source Rebuild
→ Re-download

### Recovery Rules

1. Attempt local repair first.
2. Attempt backup recovery second.
3. Attempt source regeneration third.
4. Attempt external download last.

---

## Bhavcopy Framework

Bhavcopy files are designated as the Primary Market Data Source.

All derived datasets shall originate from Bhavcopy whenever possible.

### Daily Validation

On every execution:

* Check Missing Dates
* Check Corrupt Files
* Check Invalid Trading Days
* Check Registry Consistency

### Market Close Rule

During trading hours:

Current day Bhavcopy is not expected.

After market close:

Current day Bhavcopy is expected.

Target availability time:

19:00 IST onwards.

### Historical Coverage Rule

Coverage target:

1995 → Current Date

excluding:

* Weekends
* NSE Holidays

---

## Cache Framework

Cache is a performance layer only.

Cache is never considered a primary data source.

### Cache Recovery

If cache becomes:

* Missing
* Corrupted
* Incomplete

the platform shall:

* Delete Cache
* Rebuild Cache

from source datasets.

---

## Backup Framework

Backups are mandatory.

Users shall never be responsible for remembering to create backups.

### Backup Schedule

Weekly Incremental Backup

Every Friday at 23:59 IST (post market close).

### Backup Type

Incremental backups only.

No routine full backup is required.

---

## Backup Coverage

Backup shall include:

* Raw Bhavcopy Data
* Reference Data
* Classification Data
* Corporate Data
* Historical Snapshots
* Derived Intelligence
* Configuration Files
* Logs

---

## Secondary Backup

A secondary backup repository is mandatory.

Purpose:

Disaster Recovery

Protection against:

* Disk Failure
* Accidental Deletion
* Corruption
* User Error

---

## Audit Trail

Every recovery operation shall be logged.

Examples:

* Missing File Detected
* Backup Restored
* Rows Recovered
* Timestamp

---

## Design Principles

The platform shall:

* Detect Problems Automatically
* Recover Automatically
* Validate Automatically
* Backup Automatically

The platform shall not rely upon:

* Manual User Monitoring
* Manual User Backup
* Manual User Recovery

---

## Approved Outcome

The platform becomes:

* Self-Monitoring
* Self-Healing
* Recoverable
* Auditable

for all current and future engines.
