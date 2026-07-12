# Vegas Total Solution Doc Architecture

This foundation uses a plugin-first desktop shell. The `MainWindow` owns only navigation and workspace composition; feature modules are discovered by the plugin loader and rendered through the `Plugin` interface. Plugin failures are isolated and recorded so one broken module does not prevent healthy modules from loading.

## Boundaries

- `app`: application composition and process entry point.
- `core`: safe non-secret configuration, idempotent rotating logging, PyInstaller-compatible resources, theming, exceptions, context, and type-keyed dependency injection.
- `plugins`: plugin interfaces, loader, manager, registry, and reusable placeholder plugin classes.
- `builtin_plugins`: installed placeholder modules for each requested navigation item.
- `ui`: Qt shell widgets only.
- `services`, `models`, `utils`, `resources`, `config`: reserved foundation packages for future production services and types.

Business automation for DQ, OCR, Word, PDF, Excel, and document generation is intentionally not implemented in this task.
