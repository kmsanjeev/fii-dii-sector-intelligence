# ADR-018: Market Data Reliability Framework

## Status

Accepted

---

## Context

The Capital Flow Intelligence Platform depends entirely on the accuracy, completeness, and availability of market data.

Incorrect, incomplete, corrupted, or missing market data can lead to:

- Incorrect intelligence generation
- Incorrect sector rotation signals
- Incorrect participant analysis
- Incorrect AI insights
- Incorrect investment decisions

Therefore, data reliability is not a maintenance activity.

Data reliability is a core runtime dependency of the platform.

The platform shall never assume that data is valid merely because a file exists.

---

## Decision

The platform shall implement a Market Data Reliability Framework consisting of:

1. Data Integrity Validation
2. Automatic Recovery
3. Automated Incremental Backup
4. Disaster Recovery Procedures
5. Continuous Data Availability Monitoring

All market intelligence engines shall depend upon validated data only.

No intelligence processing shall begin before required data validation checks have passed.

---

# Principle 1: Data First Architecture

The platform shall treat data as the primary asset.

All analysis, intelligence, AI processing, reporting, and execution layers depend upon validated data.

If data integrity fails:

- Processing shall stop
- Recovery procedures shall begin
- Invalid intelligence shall never be generated

---

# Principle 2: Runtime Integrity Validation

Data integrity validation shall execute before processing.

The platform shall continuously verify:

- File existence
- File readability
- File structure
- Data completeness
- Data consistency

Validation is not a periodic activity.

Validation is a runtime requirement.

---

# Principle 3: Self-Healing Architecture

The platform shall automatically recover from:

- Missing files
- Corrupted files
- Incomplete files
- Invalid files

Manual intervention shall be the final recovery option.

Automatic recovery shall always be attempted first.

---

# Principle 4: Single Source of Truth

Raw market data remains the authoritative source.

Examples:

- Equity Bhavcopy
- F&O Bhavcopy
- Corporate Actions
- Shareholding Data
- Results Data
- Announcements

Derived datasets shall never become authoritative sources.

All derived datasets must remain reproducible from raw data.

---

# Principle 5: Metadata-Only Registry

Registry files shall contain metadata only.

Registry files shall not duplicate market data.

Registry responsibilities include:

- Availability monitoring
- Coverage reporting
- Integrity status
- Validation metadata
- Recovery metadata

---

# Principle 6: Data Classification

All platform data shall be classified into one of the following categories.

## Critical Data

Loss significantly impacts platform operation.

Examples:

- Raw market data
- Reference data
- Mapping files
- Configuration files
- Documentation
- Research assets

Critical data requires backup.

---

## Recoverable Data

Can be recreated but recovery is costly.

Examples:

- Historical market repositories
- Large downloaded datasets

Recoverable data requires backup.

---

## Rebuildable Data

Can be recreated automatically.

Examples:

- Cache files
- Intelligence outputs
- Aggregations
- Derived reports

Rebuildable data shall not be backed up.

---

# Principle 7: Automated Incremental Backup

Backups shall never depend on manual execution.

All backup operations shall be platform-managed.

Default backup strategy:

Incremental Backup

Frequency:

Weekly

Schedule:

Friday 23:59 IST
(Saturday 00:00 IST)

The backup process shall capture:

- New files
- Modified files
- Deleted file metadata

Only changed data shall be copied.

---

# Principle 8: Weekly Recovery Point

The weekly backup becomes the official recovery point.

All integrity audits and recovery activities shall occur only after successful backup completion.

Workflow:

Weekly Backup
    ↓
Integrity Audit
    ↓
Recovery Actions
    ↓
Maintenance Tasks
    ↓
Health Reporting

---

# Principle 9: Secondary Backup Repository

The platform shall maintain a secondary backup repository.

Examples:

- Secondary Drive
- NAS Storage
- Cloud Storage

Secondary backup creation shall be a mandatory maintenance activity.

Backup creation shall never depend on user action.

---

# Principle 10: Backup Validation

A backup is not considered valid merely because it exists.

The platform shall verify:

- File existence
- File readability
- File size validation
- Checksum validation
- Manifest validation

Corrupted backup files shall be treated as failed backups.

---

# Principle 11: Data Availability Monitoring

The platform shall continuously monitor expected market data availability.

Monitoring includes:

- Missing files
- Missing dates
- Missing trading sessions
- Corrupted files
- Incomplete datasets

The platform shall compare:

Expected Data Universe

versus

Available Data Universe

and report all discrepancies.

---

# Principle 12: Disaster Recovery Hierarchy

Recovery actions shall follow the following order.

Level 1

Restore from Secondary Backup

---

Level 2

Restore from Archived Backup

---

Level 3

Download from Official Source

---

Level 4

Rebuild from Available Raw Data

---

Level 5

Manual Recovery

---

# Principle 13: Future Maintenance Engine

A dedicated maintenance engine shall manage:

- Backup execution
- Integrity validation
- Data repair
- Cache maintenance
- Health reporting

Future Module:

engines/maintenance_engine.py

---

# Consequences

Benefits:

- Reliable market intelligence
- Automatic recovery
- Minimal manual intervention
- Reduced operational risk
- Long-term maintainability
- Disaster recovery readiness

Trade-offs:

- Additional storage requirements
- Additional maintenance processing
- Increased implementation complexity

These trade-offs are acceptable because data reliability is foundational to platform correctness.

---

## Related ADRs

ADR-001 Raw Data Never Modified

ADR-003 On-Demand Cache

ADR-004 Listing Date Aware Processing

ADR-012 Research Before Development

ADR-015 Documentation Mandatory Before Release