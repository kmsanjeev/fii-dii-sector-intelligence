from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engines.ai.knowledge.contracts import CONTRACT_VERSION, normalize_knowledge_record
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class UnifiedCorpusBuilder:
    def __init__(
        self,
        *,
        platform_docs_path: Path | None = None,
        core_docs_path: Path | None = None,
        reviewed_docs_path: Path | None = None,
        capability_docs_path: Path | None = None,
        unified_docs_path: Path | None = None,
        manifest_path: Path | None = None,
        metadata_path: Path | None = None,
    ):
        self._platform_docs_path = Path(platform_docs_path or (cfg.INTELLIGENCE_DIR / "rag_knowledge" / "documents.jsonl"))
        self._core_docs_path = Path(core_docs_path or cfg.VEDA_APPROVED_CORE_KNOWLEDGE_DOCS)
        self._reviewed_docs_path = Path(reviewed_docs_path or cfg.VEDA_APPROVED_KNOWLEDGE_DOCS)
        self._capability_docs_path = Path(capability_docs_path or cfg.VEDA_APPROVED_CAPABILITY_DOCS)
        self._unified_docs_path = Path(unified_docs_path or cfg.VEDA_UNIFIED_KNOWLEDGE_DOCS)
        self._manifest_path = Path(manifest_path or cfg.VEDA_UNIFIED_KNOWLEDGE_MANIFEST)
        self._metadata_path = Path(metadata_path or cfg.VEDA_UNIFIED_KNOWLEDGE_METADATA)

    def run(self) -> dict[str, Any]:
        records = []
        inputs = {
            "platform_docs": self._platform_docs_path,
            "approved_core_docs": self._core_docs_path,
            "reviewed_memory_docs": self._reviewed_docs_path,
            "mit_capability_docs": self._capability_docs_path,
        }
        input_counts: dict[str, int] = {}

        for label, path in inputs.items():
            raw_docs = self._load_jsonl(path)
            input_counts[label] = len(raw_docs)
            for doc in raw_docs:
                records.append(normalize_knowledge_record(doc))

        source_counts = self._count_by(records, "source_type")
        domain_counts = self._count_by(records, "domain")
        duplicates = self._find_duplicates(records)
        missing = self._find_missing(records)

        self._unified_docs_path.parent.mkdir(parents=True, exist_ok=True)
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self._metadata_path.parent.mkdir(parents=True, exist_ok=True)

        self._write_docs(records)
        self._write_metadata(records)

        summary = {
            "contract_version": CONTRACT_VERSION,
            "built_at": _utc_now(),
            "total_records": len(records),
            "input_counts": input_counts,
            "source_counts": source_counts,
            "domain_counts": domain_counts,
            "duplicate_group_count": len(duplicates),
            "duplicate_record_count": sum(item["count"] for item in duplicates),
            "missing_critical_field_count": len(missing),
            "duplicates": duplicates,
            "missing_critical_fields": missing,
            "output_paths": {
                "documents": str(self._unified_docs_path),
                "manifest": str(self._manifest_path),
                "metadata": str(self._metadata_path),
            },
        }
        self._write_manifest(summary)
        logger.info(
            "[UnifiedCorpus] Built %s records from platform=%s core=%s reviewed=%s capability=%s",
            len(records),
            input_counts["platform_docs"],
            input_counts["approved_core_docs"],
            input_counts["reviewed_memory_docs"],
            input_counts["mit_capability_docs"],
        )
        return summary

    def _load_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            logger.info("[UnifiedCorpus] Input file missing, skipping: %s", path)
            return []
        docs: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("[UnifiedCorpus] Skipping invalid JSONL line from %s", path)
        return docs

    def _count_by(self, records, field_name: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            key = str(getattr(record, field_name) or "UNKNOWN")
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: (item[0], item[1])))

    def _find_duplicates(self, records) -> list[dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        for record in records:
            fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "domain": record.domain,
                        "entity": record.entity,
                        "text": record.text,
                        "summary": record.summary,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()[:16]
            entry = groups.setdefault(
                fingerprint,
                {
                    "fingerprint": fingerprint,
                    "count": 0,
                    "doc_ids": [],
                    "source_types": [],
                    "domain": record.domain,
                    "entity": record.entity,
                },
            )
            entry["count"] += 1
            entry["doc_ids"].append(record.doc_id)
            if record.source_type not in entry["source_types"]:
                entry["source_types"].append(record.source_type)

        duplicates = [item for item in groups.values() if item["count"] > 1]
        duplicates.sort(key=lambda item: (-item["count"], item["entity"], item["fingerprint"]))
        return duplicates

    def _find_missing(self, records) -> list[dict[str, Any]]:
        missing: list[dict[str, Any]] = []
        for record in records:
            fields = []
            if not record.doc_id:
                fields.append("doc_id")
            if not record.source_type:
                fields.append("source_type")
            if not record.domain:
                fields.append("domain")
            if not record.entity:
                fields.append("entity")
            if not record.text:
                fields.append("text")
            if not record.summary:
                fields.append("summary")
            if not record.provenance.source_kind:
                fields.append("provenance.source_kind")
            if fields:
                missing.append(
                    {
                        "doc_id": record.doc_id,
                        "source_type": record.source_type,
                        "missing_fields": fields,
                    }
                )
        return missing

    def _write_docs(self, records) -> None:
        tmp = self._unified_docs_path.with_suffix(".tmp.jsonl")
        with open(tmp, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        tmp.replace(self._unified_docs_path)

    def _write_manifest(self, summary: dict[str, Any]) -> None:
        tmp = self._manifest_path.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._manifest_path)

    def _write_metadata(self, records) -> None:
        tmp = self._metadata_path.with_suffix(".tmp.csv")
        with open(tmp, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "doc_id",
                    "source_type",
                    "domain",
                    "entity",
                    "text_len",
                    "tag_count",
                    "saved_at",
                    "effective_date",
                    "freshness_class",
                    "approval_state",
                ],
            )
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "doc_id": record.doc_id,
                        "source_type": record.source_type,
                        "domain": record.domain,
                        "entity": record.entity,
                        "text_len": len(record.text),
                        "tag_count": len(record.tags),
                        "saved_at": record.saved_at or "",
                        "effective_date": record.effective_date or "",
                        "freshness_class": record.freshness_class,
                        "approval_state": record.approval_state,
                    }
                )
        tmp.replace(self._metadata_path)
