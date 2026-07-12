"""python-docx based DQ document generator."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentObject
from docx.shared import Inches
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

from vegas_doc.models.dq_mapping import DQMapping
from vegas_doc.models.urs import URSRequirement

REQUIREMENTS_TABLE_TOKEN = "[##DQ_REQUIREMENTS_TABLE##]"
TRACEABILITY_TABLE_TOKEN = "[##TRACEABILITY_TABLE##]"


class DQDocxGenerator:
    """Generate reviewed DQ documents without modifying the template."""

    def ensure_default_template(self, template_path: Path) -> Path:
        """Create a deterministic replaceable default template when missing."""

        if template_path.exists():
            return template_path
        template_path.parent.mkdir(parents=True, exist_ok=True)
        document = Document()
        document.add_heading("Design Qualification", 0)
        document.add_paragraph("Project: ##PROJECT_NAME##")
        document.add_paragraph("Document Number: ##DOCUMENT_NUMBER##")
        document.add_heading("Reviewed Requirements", level=1)
        document.add_paragraph(REQUIREMENTS_TABLE_TOKEN)
        document.add_heading("Traceability", level=1)
        document.add_paragraph(TRACEABILITY_TABLE_TOKEN)
        document.save(template_path)
        return template_path

    def generate(self, template_path: Path, output_path: Path, context: dict[str, str], requirements: tuple[URSRequirement, ...], mappings: tuple[DQMapping, ...]) -> Path:
        """Generate a DOCX atomically and clean temporary files on failure."""

        source_template = self.ensure_default_template(template_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix="vegas_dq_docx_", dir=output_path.parent))
        temp_output = temp_dir / output_path.name
        try:
            document = Document(source_template)
            replacements = {f"##{key.upper()}##": value for key, value in context.items()}
            _replace_everywhere(document, replacements)
            _replace_token_with_requirements_table(document, requirements)
            _replace_token_with_traceability_table(document, mappings)
            document.save(temp_output)
            temp_output.replace(output_path)
            return output_path
        except Exception:
            if temp_output.exists():
                temp_output.unlink(missing_ok=True)
            raise
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _replace_everywhere(document: DocumentObject, mapping: dict[str, str]) -> None:
    for paragraph in _all_paragraphs(document):
        _replace_in_paragraph(paragraph, mapping)


def _all_paragraphs(document: DocumentObject):  # type: ignore[no-untyped-def]
    for paragraph in document.paragraphs:
        yield paragraph
    for table in document.tables:
        for paragraph in _table_paragraphs(table):
            yield paragraph
    for section in document.sections:
        for part in (section.header, section.footer):
            for paragraph in part.paragraphs:
                yield paragraph
            for table in part.tables:
                for paragraph in _table_paragraphs(table):
                    yield paragraph


def _table_paragraphs(table: Table):  # type: ignore[no-untyped-def]
    for row in table.rows:
        for cell in row.cells:
            yield from _cell_paragraphs(cell)


def _cell_paragraphs(cell: _Cell):  # type: ignore[no-untyped-def]
    for paragraph in cell.paragraphs:
        yield paragraph
    for table in cell.tables:
        yield from _table_paragraphs(table)


def _replace_in_paragraph(paragraph: Paragraph, mapping: dict[str, str]) -> None:
    text = "".join(run.text for run in paragraph.runs)
    changed = text
    for key, value in mapping.items():
        changed = changed.replace(key, value)
    if changed == text:
        return
    for run in paragraph.runs:
        run.text = ""
    if paragraph.runs:
        paragraph.runs[0].text = changed
    else:
        paragraph.add_run(changed)


def _replace_token_with_requirements_table(document: DocumentObject, requirements: tuple[URSRequirement, ...]) -> None:
    paragraph = _find_paragraph(document, REQUIREMENTS_TABLE_TOKEN)
    if paragraph is None:
        return
    paragraph.text = ""
    table = _insert_table_after(paragraph, 1, 6)
    headers = ["ID", "Page", "Category", "Requirement", "DQ Response", "Verification"]
    for index, header in enumerate(headers):
        table.cell(0, index).text = header
    for requirement in [item for item in requirements if item.included and item.user_reviewed]:
        cells = table.add_row().cells
        cells[0].text = requirement.requirement_id
        cells[1].text = str(requirement.source_page)
        cells[2].text = requirement.category or "General"
        cells[3].text = requirement.normalized_text
        cells[4].text = requirement.dq_section or ""
        cells[5].text = requirement.verification_method.value


def _replace_token_with_traceability_table(document: DocumentObject, mappings: tuple[DQMapping, ...]) -> None:
    paragraph = _find_paragraph(document, TRACEABILITY_TABLE_TOKEN)
    if paragraph is None:
        return
    paragraph.text = ""
    table = _insert_table_after(paragraph, 1, 4)
    headers = ["Mapping", "URS IDs", "DQ Sections", "Relationship"]
    for index, header in enumerate(headers):
        table.cell(0, index).text = header
    for mapping in mappings:
        cells = table.add_row().cells
        cells[0].text = mapping.mapping_id
        cells[1].text = ", ".join(mapping.source_requirement_ids)
        cells[2].text = ", ".join(mapping.dq_section_ids)
        cells[3].text = mapping.relationship.value


def _find_paragraph(document: DocumentObject, token: str) -> Paragraph | None:
    for paragraph in _all_paragraphs(document):
        if token in paragraph.text:
            return paragraph
    return None


def _insert_table_after(paragraph: Paragraph, rows: int, cols: int) -> Table:
    try:
        table = paragraph._parent.add_table(rows=rows, cols=cols, width=Inches(6.5))  # noqa: SLF001 - python-docx insertion requires XML placement
    except TypeError:
        table = paragraph._parent.add_table(rows=rows, cols=cols)  # noqa: SLF001
    paragraph._p.addnext(table._tbl)  # noqa: SLF001
    return table
