# Package Size Optimization

## Safety boundaries

The optimization retains PySide6 QtCore, QtGui, and QtWidgets; Windows platform and image plugins; application resources; builtin plugin modules; PyMuPDF; python-docx; requests; and the Windows keyring backend. One-folder mode and console-free startup are preserved.

## Confirmed exclusions

Excluded Qt modules are optional 3D, Bluetooth, charts, data visualization, graphs, help, location, multimedia, QML/Quick, PDF UI, sensors, serial, SQL, text-to-speech, WebEngine/WebSockets, test, and designer-oriented modules not imported by the application.

Development-only Python packages such as pytest, pip, setuptools, wheel, notebook/Jupyter, scientific/plotting stacks, docs tooling, and tkinter are excluded from the frozen runtime. Linux/macOS keyring integrations are excluded while `keyring.backends.Windows` is retained explicitly.

Post-build cleanup keeps the Windows platform plugin, common image codecs, styles, TLS plugins, and Korean/English Qt translations. It removes unrelated plugin categories, translations, test/cache content, PDBs, and source maps.

## Compression and UPX

Inno Setup uses `lzma2/ultra64`, solid compression, and a separate LZMA process. UPX remains disabled: Qt DLL compression can harm runtime stability and increase antivirus false-positive risk. It should only be reconsidered after a separately measured, signed-build validation.

## Measurement

The workflow generates baseline and optimized packages on the same `windows-latest` runner and writes exact byte/MiB values plus the 30 largest files to:

- `artifacts/package_size_before.txt`
- `artifacts/package_size_after.txt`

It warns above 120 MiB and fails only above 160 MiB. The reports are uploaded as the `package-size-report` artifact.
