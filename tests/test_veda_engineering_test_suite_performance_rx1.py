from pathlib import Path

from engines.common.repository_inventory import GOVERNED_INVENTORY_ROOTS, iter_inventory_files
from scripts.veda_engineering_test_suite_performance_rx1_001 import GROUP_ORDER, inventory


ROOT = Path(__file__).resolve().parents[1]


def test_governed_inventory_scope_excludes_operational_bulk_payloads() -> None:
    files = {path.relative_to(ROOT).as_posix() for path in iter_inventory_files(ROOT)}
    assert files
    assert any(path.startswith("engines/") for path in files)
    assert not any(path.startswith("data/NSE/") for path in files)
    assert not any(path.startswith("data/intelligence/") for path in files)
    assert all(any(path == root or path.startswith(root + "/") for root in GOVERNED_INVENTORY_ROOTS) for path in files)


def test_temporary_inventory_roots_keep_recursive_fixture_behavior(tmp_path: Path) -> None:
    sample = tmp_path / "nested" / "sample.py"
    sample.parent.mkdir()
    sample.write_text("sample = True\n", encoding="utf-8")
    assert list(iter_inventory_files(tmp_path)) == [sample]


def test_profile_catalog_is_disjoint_and_covers_all_test_files() -> None:
    catalog = inventory()
    groups = catalog["groups"]
    assert catalog["group_order"] == list(GROUP_ORDER)
    flattened = [path for details in groups.values() for path in details["files"]]
    assert len(flattened) == len(set(flattened)) == catalog["test_files"]
