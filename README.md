# Vegas Total Solution Doc

Commercial-grade internal document automation platform foundation for Vegas Inc.

> Existing GreenMetal Automation Suite business behavior is preserved in `src/legacy_main.py` for reference only. The active application entry point is now the plugin-based Vegas Total Solution Doc shell.

## Foundation delivered

- PySide6 desktop shell with left navigation and right plugin workspace.
- Plugin contract, loader, registry, and manager.
- Placeholder plugins only for Manual Generator, DQ Generator, IQ Generator, OQ Generator, PQ Generator, URS OCR, PLC Generator, Alarm Generator, Excel Helper, and Settings.
- Core services for configuration, rotating daily logging, resource resolution, theming, exception handling, application context, and dependency injection.
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

Configuration is JSON and non-secret only. Runtime logs are written to the per-user application data directory under `logs/yyyy-mm-dd.log` with `RotatingFileHandler`. Secrets must be stored through an approved secret store in future feature work, never in config files or the repository.

## Not implemented in this foundation

No DQ generation, OCR, Word, PDF, Excel, PLC, alarm, or document-generation business behavior is implemented here.
