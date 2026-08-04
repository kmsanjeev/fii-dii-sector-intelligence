from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from engines.ai.attachments.service import AttachmentService
from engines.common import config as cfg


def _enable_attachment_settings(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENTS_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_FILE_BYTES", 2 * 1024 * 1024)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_TEXT_CHARS", 6000)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_TOTAL_PROMPT_CHARS", 9000)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_EXCERPT_CHARS", 180)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_TABLE_ROWS", 10)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_TABLE_COLS", 8)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_FILES", 4)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_PDF_PAGES", 3)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_VISION_ENABLED", False)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_VISION_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_VISION_MAX_TOKENS", 200)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_VISION_TIMEOUT_S", 10)


def test_attachment_service_extracts_plain_text(monkeypatch, tmp_dir):
    _enable_attachment_settings(monkeypatch)
    service = AttachmentService(upload_dir=tmp_dir)

    uploaded = service.save_upload(
        filename="notes.txt",
        content_type="text/plain",
        content=b"Net profit grew 12 percent year over year.",
    )

    assert uploaded.kind == "text"
    assert "Net profit grew" in uploaded.extracted_text
    loaded = service.load(uploaded.storage_key)
    assert loaded.name == "notes.txt"


def test_attachment_service_extracts_csv_preview(monkeypatch, tmp_dir):
    _enable_attachment_settings(monkeypatch)
    service = AttachmentService(upload_dir=tmp_dir)

    uploaded = service.save_upload(
        filename="flows.csv",
        content_type="text/csv",
        content=b"symbol,fii_net,dii_net\nTCS,120,80\nINFY,90,40\n",
    )

    assert uploaded.kind == "csv"
    assert "symbol | fii_net | dii_net" in uploaded.extracted_text
    assert "TCS | 120 | 80" in uploaded.extracted_text


def test_attachment_service_builds_prompt_context(monkeypatch, tmp_dir):
    _enable_attachment_settings(monkeypatch)
    service = AttachmentService(upload_dir=tmp_dir)
    uploaded = service.save_upload(
        filename="summary.json",
        content_type="application/json",
        content=b'{"company":"TCS","signal":"bullish","confidence":0.82}',
    )

    context = service.build_prompt_context([
        SimpleNamespace(**uploaded.to_chat_stub()),
    ])

    assert "Uploaded files below are user-provided content sources" in context
    assert "summary.json" in context
    assert '"company": "TCS"' in context


def test_attachment_service_extracts_image_metadata(monkeypatch, tmp_dir):
    _enable_attachment_settings(monkeypatch)
    Image = pytest.importorskip("PIL.Image")
    service = AttachmentService(upload_dir=tmp_dir)

    img = Image.new("RGB", (64, 32), color=(12, 34, 56))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    uploaded = service.save_upload(
        filename="chart.png",
        content_type="image/png",
        content=buf.getvalue(),
    )

    assert uploaded.kind == "image"
    assert "Image uploaded: chart.png" in uploaded.extracted_text
    assert "64 x 32" in uploaded.extracted_text


def test_attachment_service_extracts_image_vision_summary(monkeypatch, tmp_dir):
    _enable_attachment_settings(monkeypatch)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_VISION_ENABLED", True)
    Image = pytest.importorskip("PIL.Image")
    service = AttachmentService(upload_dir=tmp_dir)

    monkeypatch.setattr(
        AttachmentService,
        "_try_image_vision",
        lambda self, *, content, mime_type, filename: ("The image looks like a sector rotation heatmap with banking in the lead.", None),
    )
    monkeypatch.setattr(AttachmentService, "_try_image_ocr", lambda self, image: "")

    img = Image.new("RGB", (80, 40), color=(30, 60, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    uploaded = service.save_upload(
        filename="rotation.png",
        content_type="image/png",
        content=buf.getvalue(),
    )

    assert "Vision summary:" in uploaded.extracted_text
    assert "sector rotation heatmap" in uploaded.extracted_text
    assert uploaded.warning is None
