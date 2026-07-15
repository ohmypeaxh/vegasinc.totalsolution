# Windows package size optimization

The release build remains one-folder PyInstaller plus an Inno Setup installer. This keeps Qt
plugin discovery, keyring backends, plugin loading, and resource lookup reliable.

The spec excludes only confirmed-unused optional packages and Qt modules. Core, GUI, Widgets,
Network, image formats, PDF extraction binaries, DOCX dependencies, requests, and Windows
keyring support remain included. UPX is disabled because Qt DLL compression can cause startup
or antivirus problems; this is a deliberate reliability choice.

Inno Setup uses `lzma2/ultra64`, solid compression, and a separate compression process.
GitHub Actions builds the optimized spec and reports distribution size, actual installer
size, and the twenty largest packaged files. The preferred installer target is 100 MB or
less. The job emits an additional warning above 120 MB and fails above the 160 MB hard
limit. Exact values must come from the Windows workflow artifact; estimates are not reported.
