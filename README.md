# Vegas Total Solution Doc

Commercial-grade internal document automation platform foundation for Vegas Inc.

> Existing GreenMetal Automation Suite business behavior is preserved in `src/legacy_main.py` for reference only. The active application entry point is now the plugin-based Vegas Total Solution Doc shell.

## Foundation delivered

- PySide6 desktop shell with left navigation and right plugin workspace.
- Plugin contract, loader, registry, and manager with duplicate-ID rejection, deterministic ordering, and broken-plugin isolation.
- Placeholder plugins only for Manual Generator, DQ Generator, IQ Generator, OQ Generator, PQ Generator, URS OCR, PLC Generator, Alarm Generator, Excel Helper, and Settings.
- Core services for safe non-secret configuration, rotating daily logging, PyInstaller-compatible resource resolution, safe theming, exception handling, application context, and type-keyed dependency injection.
- Pytest startup and plugin-loading tests.

## Architecture

```text
src/vegas_doc/
  app/              # application entry point and composition
  core/             # infrastructure services
  plugins/          # plugin framework
  builtin_plugins/  # installed placeholder modules
  services/         # future service abstractions
  ui/               # Qt shell UI
  resources/        # packaged resources
  config/           # defaults and config types
  models/           # future dataclasses/domain models
  utils/            # utility helpers
tests/              # automated tests
docs/               # architecture notes
scripts/            # automation scripts
```

## Development

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -e .[dev]
pytest
python -m vegas_doc.app.main
```

## Configuration and secrets

Configuration is JSON and non-secret only. Missing, empty, malformed, or non-object user configuration falls back to defaults and is logged when a logger is available. Runtime files are written to a Windows-writable per-user application data directory, never to the installed application directory. Runtime logs are written under `logs/yyyy-mm-dd.log` with UTF-8 `RotatingFileHandler`. Secrets must be stored through an approved secret store in future feature work, never in config files or the repository.

## Phase 2 DQ domain foundation

Phase 2 adds provider-neutral OCR contracts, document extraction contracts, URS requirement models, DQ mapping models, and versioned JSON project persistence. It remains domain/service-only: no UI workflow, CLOVA HTTP integration, OCR/parsing/classification/mapping algorithms, or Word generation is implemented. See `docs/phase2_dq_domain.md`.

## DQ Generator end-to-end workflow

1. Clone the repository and checkout `feature/dq-ocr-end-to-end`.
2. Run `scripts\setup_dev.bat` on Windows with Python 3.12.
3. Start the app with `scripts\run_dev.bat`.
4. Open **Settings**, enter the NAVER CLOVA Invoke URL, timeout, and secret key. The URL can also come from `VEGAS_CLOVA_INVOKE_URL`; the secret can come from `VEGAS_CLOVA_SECRET_KEY`. Secrets are stored with keyring and are never written to project files.
5. Use **Test Connection** to send a generated readable test image.
6. Open **DQ Generator**, enter project information, import a PDF/PNG/JPG/JPEG/TIF/TIFF URS source, run extraction, review/edit requirements and responses, save/reopen `.vdqproj`, then generate a `.docx`.
7. If OCR fails for one page, continue reviewing successful pages and retry after fixing settings. Korean user-facing errors appear in the UI; English technical details are written to logs.

Troubleshooting: verify Python 3.12, run `scripts\test.bat`, confirm keyring access, ensure the output directory is writable, and use searchable PDFs where possible to avoid unnecessary OCR.

## Not implemented in this foundation

No DQ generation, OCR, Word, PDF, Excel, PLC, alarm, or document-generation business behavior is implemented here.


## UI preview screenshots

The preview workflow renders the real PySide6 application widgets with Qt's offscreen
platform. It uses synthetic project and URS data, masks credentials, and uploads PNG
screenshots without calling CLOVA OCR.

### GitHub

1. Open **Actions**.
2. Select **Generate UI Previews**.
3. Select **Run workflow**.
4. Download the **Vegas-Total-Solution-Doc-UI-Previews** artifact after the run completes.

### Local Windows

Install the development dependencies, then run:

```bat
scripts\preview_ui.bat
```

The screenshots are written to `artifacts/ui-previews/`.
