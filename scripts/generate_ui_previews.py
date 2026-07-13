"""Generate privacy-safe screenshots of the real PySide6 application widgets."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.pop("VEGAS_CLOVA_INVOKE_URL", None)
os.environ.pop("VEGAS_CLOVA_SECRET_KEY", None)

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QScrollArea, QWidget

from vegas_doc.app.main import create_main_window, get_or_create_application
from vegas_doc.builtin_plugins.dq_generator import DQGeneratorWidget
from vegas_doc.builtin_plugins.fds_generator import FDSGeneratorWidget
from vegas_doc.builtin_plugins.settings import SettingsWidget
from vegas_doc.core.application_context import build_application_context
from vegas_doc.core.theme_manager import ThemeManager
from vegas_doc.models.dq_mapping import DQResponse
from vegas_doc.models.fds_document import FDSStatement
from vegas_doc.models.urs import URSRequirement
from vegas_doc.ui.about_dialog import AboutDialog
from vegas_doc.ui.onboarding_wizard import OnboardingWizard

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "artifacts" / "ui-previews"
EXPECTED_SCREENSHOTS = (
    "01_main_window.png",
    "02_dq_generator_project_info.png",
    "03_dq_generator_urs_import.png",
    "04_dq_generator_ocr_review.png",
    "05_dq_generator_requirement_review.png",
    "06_dq_generator_template_output.png",
    "07_settings_ocr.png",
    "08_first_run_onboarding.png",
    "09_about_dialog.png",
    "10_fds_generator.png",
    "11_fds_rules.png",
)


def _process_events(app: QApplication) -> None:
    """Flush pending layout and paint events before grabbing a widget."""

    for _ in range(3):
        app.processEvents()


def _scroll_to_widget(scroll: QScrollArea, widget: QWidget, top_margin: int = 20) -> None:
    """Place the target widget near the top of its real scroll viewport."""

    content = scroll.widget()
    if content is None:
        return
    target_y = widget.mapTo(content, QPoint(0, 0)).y()
    scroll.verticalScrollBar().setValue(max(0, target_y - top_margin))


def _save_widget(widget, filename: str, app: QApplication) -> None:  # type: ignore[no-untyped-def]
    """Render an actual QWidget to a PNG and fail if Qt cannot save it."""

    _process_events(app)
    destination = OUTPUT_DIRECTORY / filename
    if not widget.grab().save(str(destination), "PNG"):
        raise RuntimeError(f"Qt could not save UI preview: {destination}")


def _select_plugin(window, plugin_id: str, app: QApplication):  # type: ignore[no-untyped-def]
    """Select a real installed plugin and return its workspace widget."""

    for row in range(window._navigation.count()):
        item = window._navigation.item(row)
        if item.data(Qt.UserRole) == plugin_id:
            window._navigation.setCurrentRow(row)
            _process_events(app)
            return window._workspace.currentWidget()
    raise RuntimeError(f"Installed plugin not found: {plugin_id}")


def _sample_requirements() -> tuple[URSRequirement, ...]:
    """Return synthetic, non-customer requirements for the preview."""

    source = Path("sample-data") / "demo_urs.pdf"
    return (
        URSRequirement(
            "URS-DEMO-001",
            source,
            3,
            "4.1",
            "The demo system shall record operator actions.",
            "The system shall record operator actions in an audit trail.",
            category="Data Integrity",
            dq_section="Audit Trail",
            confidence=0.98,
            user_reviewed=True,
            user_notes="Safe synthetic preview data",
        ),
        URSRequirement(
            "URS-DEMO-002",
            source,
            4,
            "4.2",
            "The demo system shall stop safely when an interlock is active.",
            "The system shall enter a safe state when an interlock is active.",
            category="Safety",
            dq_section="Safety Controls",
            confidence=0.96,
            user_reviewed=True,
        ),
    )


def generate_previews() -> None:
    """Compose the production application and capture its real widgets."""

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for old_preview in OUTPUT_DIRECTORY.glob("*.png"):
        old_preview.unlink()

    app = get_or_create_application(["generate-ui-previews"])
    app.setApplicationName("Vegas Total Solution Doc")

    with TemporaryDirectory(prefix="vegas-ui-preview-", ignore_cleanup_errors=True) as temporary_directory:
        context = build_application_context(data_dir=Path(temporary_directory))
        context.services.resolve(ThemeManager).apply(app)
        window = create_main_window(context)
        window.resize(1440, 900)
        window.show()
        _process_events(app)

        _save_widget(window, "01_main_window.png", app)

        dq_widget = _select_plugin(window, "dq", app)
        if not isinstance(dq_widget, DQGeneratorWidget):
            raise TypeError("DQ plugin did not provide the production DQGeneratorWidget")
        dq_scroll = dq_widget.findChild(QScrollArea, "WorkspaceScroll")
        if dq_scroll is None:
            raise RuntimeError("DQ workspace scroll area was not found")

        dq_widget.project_name.setText("Demo Sterile Mixing System")
        dq_widget.document_number.setText("DQ-DEMO-001")
        dq_widget.source_path.clear()
        dq_widget.page_review.clear()
        dq_widget.model.set_items((), {})
        dq_widget.status.setText("프로젝트 정보를 입력했습니다.")
        _save_widget(window, "02_dq_generator_project_info.png", app)

        dq_widget.source_path.setText(str(Path("sample-data") / "demo_urs.pdf"))
        dq_widget.status.setText("안전한 샘플 URS 파일을 가져올 준비가 되었습니다.")
        _save_widget(window, "03_dq_generator_urs_import.png", app)

        dq_widget.page_review.setPlainText(
            "[Sample OCR Review - synthetic data]\n"
            "URS-DEMO-001 The demo system shall record operator actions.\n"
            "URS-DEMO-002 The demo system shall stop safely when an interlock is active."
        )
        dq_widget.status.setText("샘플 OCR 텍스트 검토")
        _scroll_to_widget(dq_scroll, dq_widget.page_review)
        _process_events(app)
        _save_widget(window, "04_dq_generator_ocr_review.png", app)

        requirements = _sample_requirements()
        responses = {
            requirements[0].requirement_id: DQResponse(
                "RESP-URS-DEMO-001",
                "The design provides a timestamped, attributable audit trail.",
            ),
            requirements[1].requirement_id: DQResponse(
                "RESP-URS-DEMO-002",
                "The interlock design transitions the equipment to a safe state.",
            ),
        }
        dq_widget.model.set_items(requirements, responses)
        dq_widget.table.resizeColumnsToContents()
        dq_widget.status.setText("2개의 샘플 요구사항을 검토했습니다.")
        _scroll_to_widget(dq_scroll, dq_widget.table)
        _process_events(app)
        _save_widget(window, "05_dq_generator_requirement_review.png", app)

        dq_widget.template_path.setText(str(Path("templates") / "default_dq_template.docx"))
        dq_widget.output_path.setText(str(Path("output") / "DQ-DEMO-001.docx"))
        dq_widget.status.setText("템플릿 및 출력 경로 검토 완료 — 생성 준비")
        _scroll_to_widget(dq_scroll, dq_widget.output_directory_input)
        _process_events(app)
        _save_widget(window, "06_dq_generator_template_output.png", app)

        settings_widget = _select_plugin(window, "settings", app)
        if not isinstance(settings_widget, SettingsWidget):
            raise TypeError("Settings plugin did not provide the production SettingsWidget")
        settings_widget.url.setText("https://example.invalid/clova-ocr")
        settings_widget.secret.setText("preview-secret-is-masked")
        settings_widget.secret.setEchoMode(QLineEdit.EchoMode.Password)
        settings_widget.timeout.setValue(60)
        settings_widget.status.setText("미리보기용 값입니다. 실제 자격증명은 포함되지 않습니다.")
        _save_widget(window, "07_settings_ocr.png", app)

        fds_widget = _select_plugin(window, "fds", app)
        if not isinstance(fds_widget, FDSGeneratorWidget):
            raise TypeError("F&DS plugin did not provide the production FDSGeneratorWidget")
        fds_widget.equipment_name.setText("Demo Sterile Mixing System")
        fds_widget.document_number.setText("FDS-DEMO-001")
        fds_widget.urs_input.set_path(Path("sample-data") / "demo_urs.pdf")
        fds_widget.logo_input.set_path(Path("sample-data") / "vegas_demo_logo.png")
        fds_widget.template_input.set_path(Path("templates") / "demo_fds_template.docx")
        fds_widget.output_directory.set_path(Path("output"))
        fds_widget._populate_review(
            (
                FDSStatement(
                    "6.4.1",
                    3,
                    "모서리가 뾰족하지 않아야 한다.",
                    "모서리가 뾰족하지 않도록 제작한다.",
                ),
                FDSStatement(
                    "6.4.2",
                    4,
                    "작업자가 기록을 확인할 수 있어야 한다.",
                    "작업자가 기록을 확인할 수 있도록 제작한다.",
                ),
            )
        )
        fds_widget.status.setText("미리보기용 URS 2개를 변환했습니다.")
        fds_widget.tabs.setCurrentIndex(0)
        fds_scroll = fds_widget.findChild(QScrollArea, "WorkspaceScroll")
        if fds_scroll is None:
            raise RuntimeError("F&DS workspace scroll area was not found")
        _scroll_to_widget(fds_scroll, fds_widget.review_table)
        _process_events(app)
        _save_widget(window, "10_fds_generator.png", app)
        fds_widget.tabs.setCurrentIndex(1)
        _save_widget(window, "11_fds_rules.png", app)

        onboarding = OnboardingWizard(window)
        onboarding.template_path.setText(str(Path("templates") / "default_dq_template.docx"))
        onboarding.invoke_url.setText("https://example.invalid/clova-ocr")
        onboarding.secret_key.setText("preview-secret-is-masked")
        onboarding.resize(780, 520)
        onboarding.show()
        _save_widget(onboarding, "08_first_run_onboarding.png", app)
        onboarding.close()

        about = AboutDialog("0.1.0", window)
        about.resize(640, 360)
        about.show()
        _save_widget(about, "09_about_dialog.png", app)
        about.close()

        dq_widget._dirty = False
        window.close()

    missing = [name for name in EXPECTED_SCREENSHOTS if not (OUTPUT_DIRECTORY / name).is_file()]
    if missing:
        raise RuntimeError(f"Missing generated UI previews: {', '.join(missing)}")


if __name__ == "__main__":
    import traceback

    try:
        generate_previews()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
    print(f"Generated {len(EXPECTED_SCREENSHOTS)} UI previews in {OUTPUT_DIRECTORY}")
