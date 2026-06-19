"""Tests unitarios del servicio de exportación."""
from datetime import datetime

from app.services.export_service import export_docx, export_pdf, export_txt


class _FakeTr:
    def __init__(self):
        self.glosses = ["YO", "IR", "UNIVERSIDAD", "MAÑANA"]
        self.natural_text = "Mañana voy a la universidad."
        self.confidence = 0.91
        self.created_at = datetime(2026, 6, 18, 10, 30)


def test_export_txt_contains_text():
    data = export_txt([_FakeTr()])
    assert b"Maxico" not in data  # sanity
    assert "universidad".encode("utf-8") in data


def test_export_pdf_is_pdf():
    data = export_pdf([_FakeTr()])
    assert data[:4] == b"%PDF"


def test_export_docx_is_zip():
    # Los .docx son contenedores ZIP (cabecera PK)
    data = export_docx([_FakeTr()])
    assert data[:2] == b"PK"
