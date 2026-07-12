# Windows package size optimization

The release build remains one-folder PyInstaller plus an Inno Setup installer. This keeps Qt
plugin discovery, keyring backends, plugin loading, and resource lookup reliable.

The spec excludes only confirmed-unused optional packages and Qt modules. Core, GUI, Widgets,
Network, image formats, PDF extraction binaries, DOCX dependencies, requests, and Windows
keyring support remain included. UPX is disabled because Qt DLL compression can cause startup
or antivirus problems; this is a deliberate reliability choice.

Inno Setup uses `lzma2/ultra64`, solid compression, and a separate compression process.
GitHub Actions builds a before report from the prior broad PyInstaller command and an after
report from `Vegas_Total_Solution_Doc.spec`. It reports distribution size, installer size,
and the twenty largest packaged files. The release job warns above 120 MB and fails only
above 160 MB. Exact before/after values must come from the workflow artifacts; no estimates
are reported.
